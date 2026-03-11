# modules/04_video.py
import json
import time
import requests
import os
import random
import subprocess
import torch
import gc
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")

def clear_cuda_cache():
    """
    Call this between every clip generation to prevent VRAM fragmentation.
    This is the direct fix for quality degradation across long sessions.
    """
    logger.info("🧹 Clearing CUDA cache and resetting memory stats...")
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        logger.success("✅ VRAM cleaned.")
    else:
        logger.debug("CUDA not available, skipping cache clear.")

def upscale_clip(input_path: str, output_path: str) -> str:
    """Run Real-ESRGAN 2x upscale: 720p -> 1440p."""
    logger.info(f"Starting upscale: {input_path} -> {output_path}")
    try:
        subprocess.run([
            "/workspace/venv_persistent/bin/python3", "/workspace/Real-ESRGAN/inference_realesrgan_video.py",
            "-i", input_path,
            "-o", output_path,
            "--model_name", "RealESRGAN_x4plus",
            "--outscale", "2"
        ], check=True)
        logger.success(f"Upscale complete: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Upscale FAILED: {e}")
        raise

def get_running_pod_url():
    """Discover the current running pod's proxy URL."""
    import runpod
    try:
        runpod.api_key = RUNPOD_API_KEY
        pods = runpod.get_pods()
        for pod in pods:
            if pod.get('desiredStatus') == 'RUNNING' and pod.get('runtime'):
                pod_id = pod.get('id')
                return f"https://{pod_id}-8188.proxy.runpod.net"
        return COMFYUI_URL
    except Exception:
        return COMFYUI_URL

COMFYUI_URL = get_running_pod_url()

def load_workflow_template(model: str) -> dict:
    path = Path(f"workflows/{model}_template.json")
    if not path.exists():
        path = Path("workflows/wan2_template.json")
    return json.loads(path.read_text(encoding="utf-8"))

def inject_prompt(workflow: dict, prompt: str, duration_sec: float, seed: int = None) -> dict:
    import copy
    wf = copy.deepcopy(workflow)
    final_seed = seed or random.randint(0, 1125899906842624)
    
    # --- 1. PROMPTS (Nodes 89) ---
    if "89" in wf:
        wf["89"]["inputs"]["text"] = prompt

    # --- 2. SPEED OPTIMIZATIONS (SageAttention & TeaCache) ---
    # SageAttention for High-Noise (Node 75 -> Node 101)
    wf["900"] = {
        "inputs": { "model": ["75", 0], "sage_attention": "auto" },
        "class_type": "PathchSageAttentionKJ",
        "_meta": {"title": "SageAttention (High Noise)"}
    }
    if "101" in wf: wf["101"]["inputs"]["model"] = ["900", 0]

    # SageAttention for Low-Noise (Node 76 -> Node 102 & 203)
    wf["901"] = {
        "inputs": { "model": ["76", 0], "sage_attention": "auto" },
        "class_type": "PathchSageAttentionKJ",
        "_meta": {"title": "SageAttention (Low Noise)"}
    }
    if "102" in wf: wf["102"]["inputs"]["model"] = ["901", 0]
    if "203" in wf: wf["203"]["inputs"]["model"] = ["901", 0]

    # TeaCache on Stage 3 Refinement (Max Impact)
    wf["1000"] = {
        "inputs": {
            "model": ["901", 0],
            "rel_l1_thresh": 0.25,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "cache_device": "main_device",
            "coefficients": "14B"
        },
        "class_type": "WanVideoTeaCacheKJ",
        "_meta": {"title": "TeaCache (Low Noise)"}
    }
    if "203" in wf: wf["203"]["inputs"]["model"] = ["1000", 0]

    # --- 3. SEEDS ---
    for node_id, node in wf.items():
        if "seed" in node.get("inputs", {}):
            node["inputs"]["seed"] = final_seed
        elif "noise_seed" in node.get("inputs", {}):
            node["inputs"]["noise_seed"] = final_seed
            
    return wf

def submit_job(workflow: dict) -> str:
    r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=30)
    r.raise_for_status()
    return r.json()["prompt_id"]

def poll_job(prompt_id: str, timeout: int = 1200) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            if r.status_code == 200:
                history = r.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_output in outputs.values():
                        if "videos" in node_output: return node_output["videos"][0]
        except Exception: pass
        time.sleep(20)
    raise TimeoutError(f"Job {prompt_id} timed out")

def download_clip(file_info: dict, save_path: str) -> str:
    params = {"filename": file_info["filename"], "subfolder": file_info.get("subfolder", ""), "type": "output"}
    r = requests.get(f"{COMFYUI_URL}/view", params=params, timeout=60)
    r.raise_for_status()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f: f.write(r.content)
    return save_path

def generate_one_clip(prompt: str, model: str, scene_id: int,
                       topic_slug: str, duration_sec: float = 5.0):
    """Full cycle: submit → wait → download → upscale."""
    logger.info(f"Generating scene {scene_id} using {model}...")
    try:
        workflow = load_workflow_template(model)
        workflow = inject_prompt(workflow, prompt, duration_sec)
        
        prompt_id = submit_job(workflow)
        file_info = poll_job(prompt_id)
        
        base_save_path = f"output/clips/{topic_slug}_scene{scene_id:03d}.mp4"
        download_clip(file_info, base_save_path)
        
        if os.path.exists("/workspace/Real-ESRGAN/inference_realesrgan_video.py"):
            upscaled_path = f"output/clips/{topic_slug}_scene{scene_id:03d}_upscaled.mp4"
            try:
                upscale_clip(base_save_path, upscaled_path)
                base_save_path = upscaled_path
            except Exception: pass

        return base_save_path, file_info["filename"]
    finally:
        clear_cuda_cache()

if __name__ == "__main__":
    # Test generation
    if "YOUR_POD_ID" not in COMFYUI_URL:
        generate_one_clip("Test prompt", "wan2", 1, "test_slug")
