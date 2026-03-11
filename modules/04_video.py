# modules/04_video.py
import json
import time
import requests
import os
import random
import subprocess
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")

def upscale_clip(input_path: str, output_path: str) -> str:
    """
    Run Real-ESRGAN 2x upscale: 720p -> 1440p.
    Note: This assumes it's running on the pod where Real-ESRGAN is installed in /workspace.
    """
    logger.info(f"Starting upscale: {input_path} -> {output_path}")
    try:
        subprocess.run([
            "/workspace/venv_persistent/bin/python3", "/workspace/Real-ESRGAN/inference_realesrgan_video.py",
            "-i", input_path,
            "-o", output_path,
            "--model_name", "RealESRGAN_x4plus",
            "--outscale", "2"  # 720p x2 = 1440p
        ], check=True)
        logger.success(f"Upscale complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Upscale FAILED: {e}")
        raise

def get_running_pod_url():
    """Discover the current running pod's proxy URL via runpod library."""
    import runpod
    
    logger.info("Discovering running pod URL via runpod library...")
    try:
        runpod.api_key = RUNPOD_API_KEY
        pods = runpod.get_pods()
        
        for pod in pods:
            # More robust check: desiredStatus is RUNNING and runtime exists
            if pod.get('desiredStatus') == 'RUNNING' and pod.get('runtime'):
                pod_id = pod.get('id')
                url = f"https://{pod_id}-8188.proxy.runpod.net"
                logger.success(f"Discovered active pod: {pod_id} ({url})")
                return url
        
        logger.warning("No running pod found via runpod library. Falling back to .env COMFYUI_URL.")
        return COMFYUI_URL
    except Exception as e:
        logger.error(f"Error discovering pod URL via runpod library: {e}")
        return COMFYUI_URL

# Auto-update the URL at startup
COMFYUI_URL = get_running_pod_url()

def load_workflow_template(model: str) -> dict:
    path = Path(f"workflows/{model}_template.json")
    if not path.exists():
        logger.warning(f"Template {path} not found. Falling back to workflows/wan2_template.json")
        path = Path("workflows/wan2_template.json")
    return json.loads(path.read_text(encoding="utf-8"))

def inject_prompt(workflow: dict, prompt: str, duration_sec: float, seed: int = None) -> dict:
    import copy
    wf = copy.deepcopy(workflow)
    
    # Generate seed if not provided
    final_seed = seed or random.randint(0, 1125899906842624)
    
    # --- 1. PROMPTS (Nodes 89 and 72) ---
    if "89" in wf:
        wf["89"]["inputs"]["text"] = prompt
        logger.debug("Injected positive prompt into Node 89")

    NEG_PROMPT = (
        "morphing, warping, distortion, flickering, jittering, "
        "face deformation, body distortion, painting, picture, "
        "overall gray, low quality, cartoon, anime, illustration, "
        "inconsistent lighting, multiple color grades, watermark, text"
    )
    if "72" in wf:
        wf["72"]["inputs"]["text"] = NEG_PROMPT
        logger.debug("Injected optimized negative prompt into Node 72")

    # --- 2. SPEED OPTIMIZATIONS (SageAttention & TeaCache) ---
    # We inject these between the model loaders (75/76) and the model sampling nodes (82/86)
    
    # SageAttention Injection for High-Noise Model (Node 75)
    wf["900"] = {
        "inputs": {
            "model": ["75", 0],
            "sage_attention": "enable"
        },
        "class_type": "PathchSageAttentionKJ",
        "_meta": {"title": "SageAttention (High Noise)"}
    }
    # Point Node 83 (LoRA Loader) to use Sage-patched model instead of raw model 75
    if "83" in wf:
        wf["83"]["inputs"]["model"] = ["900", 0]

    # SageAttention Injection for Low-Noise Model (Node 76)
    wf["901"] = {
        "inputs": {
            "model": ["76", 0],
            "sage_attention": "enable"
        },
        "class_type": "PathchSageAttentionKJ",
        "_meta": {"title": "SageAttention (Low Noise)"}
    }
    # Point Node 85 (LoRA Loader) to use Sage-patched model instead of raw model 76
    if "85" in wf:
        wf["85"]["inputs"]["model"] = ["901", 0]

    # TeaCache Injection (Node 1000)
    # We patch the final sampling chain right before it hits the KSamplers
    wf["1000"] = {
        "inputs": {
            "model": ["82", 0], # Patches the High Noise sampling
            "rel_l1_thresh": 0.25,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "cache_device": "main_device",
            "coefficients": "14B"
        },
        "class_type": "WanVideoTeaCacheKJ",
        "_meta": {"title": "TeaCache (High Noise)"}
    }
    # High Noise KSampler (Node 81) now uses TeaCache model
    if "81" in wf:
        wf["81"]["inputs"]["model"] = ["1000", 0]

    wf["1001"] = {
        "inputs": {
            "model": ["86", 0], # Patches the Low Noise sampling
            "rel_l1_thresh": 0.25,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "cache_device": "main_device",
            "coefficients": "14B"
        },
        "class_type": "WanVideoTeaCacheKJ",
        "_meta": {"title": "TeaCache (Low Noise)"}
    }
    # Low Noise KSampler (Node 78) now uses TeaCache model
    if "78" in wf:
        wf["78"]["inputs"]["model"] = ["1001", 0]

    # --- 3. SEEDS ---
    for node_id, node in wf.items():
        if "seed" in node.get("inputs", {}):
            node["inputs"]["seed"] = final_seed
            logger.debug(f"Injected seed into Node {node_id} (input: seed)")
        elif "noise_seed" in node.get("inputs", {}):
            node["inputs"]["noise_seed"] = final_seed
            logger.debug(f"Injected seed into Node {node_id} (input: noise_seed)")
            
    return wf

def submit_job(workflow: dict) -> str:
    try:
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["prompt_id"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            logger.error(f"ComfyUI 400 Error: {e.response.text}")
            # Optionally log the workflow to a file for inspection
            with open("logs/failed_workflow.json", "w") as f:
                json.dump(workflow, f, indent=2)
            logger.error("Failed workflow saved to logs/failed_workflow.json")
        raise

def poll_job(prompt_id: str, timeout: int = 1200) -> dict:
    """Wait for job completion, return output info (filename and subfolder)."""
    start = time.time()
    logger.info(f"Polling for job {prompt_id} (this may take several minutes)...")
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            if r.status_code == 200:
                history = r.json()
                if prompt_id in history:
                    logger.success(f"Job {prompt_id} completed!")
                    outputs = history[prompt_id].get("outputs", {})
                    for node_output in outputs.values():
                        if "videos" in node_output:
                            return node_output["videos"][0]
                        if "images" in node_output:
                            return node_output["images"][0]
        except Exception as e:
            logger.debug(f"Polling error (retrying): {e}")
            
        time.sleep(20) # Check every 20 seconds
    raise TimeoutError(f"Job {prompt_id} timed out after {timeout} seconds")

def download_clip(file_info: dict, save_path: str) -> str:
    filename = file_info["filename"]
    subfolder = file_info.get("subfolder", "")
    
    params = {"filename": filename, "subfolder": subfolder, "type": "output"}
    logger.info(f"Downloading {filename}...")
    
    r = requests.get(f"{COMFYUI_URL}/view", params=params, timeout=60)
    r.raise_for_status()
    
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(r.content)
    return save_path

def generate_one_clip(prompt: str, model: str, scene_id: int,
                       topic_slug: str, duration_sec: float = 5.0):
    """Full cycle: submit → wait → download → upscale. Returns (local file path, remote filename)."""
    logger.info(f"Generating scene {scene_id} using {model}...")
    
    workflow = load_workflow_template(model)
    workflow = inject_prompt(workflow, prompt, duration_sec)
    
    prompt_id = submit_job(workflow)
    logger.info(f"  Job submitted: {prompt_id}")
    
    file_info = poll_job(prompt_id)
    remote_filename = file_info["filename"]
    
    # Save original clip
    base_save_path = f"output/clips/{topic_slug}_scene{scene_id:03d}.mp4"
    download_clip(file_info, base_save_path)
    logger.success(f"  Saved original: {base_save_path}")
    
    # Optional: Perform Upscale (Only works if running on the pod)
    # Check if we are on the pod by checking for /workspace
    if os.path.exists("/workspace/Real-ESRGAN/inference_realesrgan_video.py"):
        upscaled_path = f"output/clips/{topic_slug}_scene{scene_id:03d}_upscaled.mp4"
        try:
            upscale_clip(base_save_path, upscaled_path)
            # Switch to upscaled path for downstream assembly
            base_save_path = upscaled_path
        except Exception:
            logger.warning("Upscaling failed, using original clip.")
    else:
        logger.info("Skipping upscale (not running on a pod with Real-ESRGAN at /workspace).")

    return base_save_path, remote_filename

if __name__ == "__main__":
    # Test: generate one clip
    test_prompt = """
    Cinematic shot of a high-tech laboratory with glowing blue interfaces, 
    robotic arms moving precisely, futuristic atmosphere, 4k, detailed textures.
    """
    
    # Check if we have a running pod before starting
    if "YOUR_POD_ID" in COMFYUI_URL:
        print("\n❌ Error: No running pod found. Please start your pod in RunPod dashboard first.")
    else:
        try:
            result = generate_one_clip(
                prompt=test_prompt,
                model="wan2",
                scene_id=1,
                topic_slug="test_discovery"
            )
            print(f"\n✅ Clip generated successfully: {result}")
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
