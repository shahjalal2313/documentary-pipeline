# modules/04_video.py
import json
import time
import requests
import os
import random
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://localhost:8188")

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
    path = f"workflows/{model}_template.json"
    return json.loads(Path(path).read_text(encoding="utf-8"))

def inject_prompt(workflow: dict, prompt: str, duration_sec: float, seed: int = None) -> dict:
    import copy
    wf = copy.deepcopy(workflow)
    
    # Generate seed if not provided
    final_seed = seed or random.randint(0, 1125899906842624)
    
    # We target specific node IDs based on the provided API JSON for wan2_template
    # Node 89: CLIPTextEncode (Positive Prompt)
    # Node 81 & 78: KSamplerAdvanced (Seeds)
    
    if "89" in wf and wf["89"].get("class_type") == "CLIPTextEncode":
        wf["89"]["inputs"]["text"] = prompt
        logger.debug("Injected prompt into Node 89")
    else:
        # Fallback: search for CLIPTextEncode with "positive" in title
        for node_id, node in wf.items():
            if node.get("class_type") == "CLIPTextEncode":
                title = node.get("_meta", {}).get("title", "").lower()
                if "positive" in title:
                    wf[node_id]["inputs"]["text"] = prompt
                    logger.debug(f"Injected prompt into Node {node_id} (fallback)")

    # Update seeds in all sampler nodes
    for node_id, node in wf.items():
        if "seed" in node.get("inputs", {}):
            node["inputs"]["seed"] = final_seed
            logger.debug(f"Injected seed into Node {node_id} (input: seed)")
        elif "noise_seed" in node.get("inputs", {}):
            node["inputs"]["noise_seed"] = final_seed
            logger.debug(f"Injected seed into Node {node_id} (input: noise_seed)")
            
    return wf

def submit_job(workflow: dict) -> str:
    response = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow},
        timeout=30
    )
    response.raise_for_status()
    return response.json()["prompt_id"]

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
                       topic_slug: str, duration_sec: float = 5.0) -> str:
    """Full cycle: submit → wait → download. Returns local file path."""
    logger.info(f"Generating scene {scene_id} using {model}...")
    
    workflow = load_workflow_template(model)
    workflow = inject_prompt(workflow, prompt, duration_sec)
    
    prompt_id = submit_job(workflow)
    logger.info(f"  Job submitted: {prompt_id}")
    
    file_info = poll_job(prompt_id)
    save_path = f"output/clips/{topic_slug}_scene{scene_id:03d}.mp4"
    
    download_clip(file_info, save_path)
    logger.success(f"  Saved: {save_path}")
    return save_path

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
