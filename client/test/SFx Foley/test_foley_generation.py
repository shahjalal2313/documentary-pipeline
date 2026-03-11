import os
import subprocess
import requests
import time
from loguru import logger
from dotenv import load_dotenv

# Project configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
POD_ID = "io253g0p0ilb70"
POD_IP = "203.57.40.62"
POD_PORT = "10093"
COMFYUI_URL = f"https://{POD_ID}-8188.proxy.runpod.net"

def free_comfy_memory():
    """Request ComfyUI to unload models and free GPU memory to avoid OOM."""
    try:
        logger.info("Requesting ComfyUI to free memory...")
        r = requests.post(f"{COMFYUI_URL}/free", json={"unload_models": True, "free_memory": True}, timeout=15)
        if r.status_code == 200:
            logger.success("GPU memory cleared successfully.")
        else:
            logger.warning(f"Free memory request returned status: {r.status_code}")
    except Exception as e:
        logger.warning(f"Could not reach ComfyUI to free memory: {e}")

def run_remote_foley(remote_filename, prompt, scene_id):
    """Trigger HunyuanVideo-Foley generation on the Pod via SSH."""
    remote_video_path = f"/workspace/runpod-slim/ComfyUI/output/video/{remote_filename}"
    remote_output_dir = "/workspace/output"
    
    # Ensure remote output directory exists
    subprocess.run(["ssh", "-p", POD_PORT, f"root@{POD_IP}", f"mkdir -p {remote_output_dir}"], check=False)
    
    model_path = "/workspace/HunyuanVideo-Foley/pretrained_models"
    config_path = "/workspace/HunyuanVideo-Foley/configs/hunyuanvideo-foley-xxl.yaml"
    
    # The command to execute on the pod - using single quotes for the prompt to avoid shell issues
    remote_cmd = (
        f"source /workspace/venv_persistent/bin/activate && "
        f"cd /workspace/HunyuanVideo-Foley && "
        f"python infer.py "
        f"--model_path {model_path} "
        f"--config_path {config_path} "
        f"--single_video {remote_video_path} "
        f"--single_prompt '{prompt}' "
        f"--output_dir {remote_output_dir} "
        f"--enable_offload"
    )
    
    ssh_cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", "-p", POD_PORT, f"root@{POD_IP}", remote_cmd
    ]
    
    logger.info(f"--- Starting Foley Generation for Scene {scene_id} ---")
    logger.info(f"Target Video: {remote_filename}")
    
    start_time = time.time()
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        logger.error(f"Remote Foley failed after {duration:.1f}s")
        logger.error(f"Error output: {result.stderr}")
        return None
    
    logger.success(f"Foley generation completed in {duration:.1f}s")
    
    # Determine the remote output filename (infer.py appends _generated.wav)
    video_base = os.path.splitext(remote_filename)[0]
    remote_foley_filename = f"{video_base}_generated.wav"
    remote_foley_path = f"{remote_output_dir}/{remote_foley_filename}"
    
    # Download the result
    local_foley_path = os.path.join(PROJECT_ROOT, "output", "clips", f"scene_{scene_id}_foley.wav")
    os.makedirs(os.path.dirname(local_foley_path), exist_ok=True)
    
    scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-P", POD_PORT, f"root@{POD_IP}:{remote_foley_path}", local_foley_path]
    logger.info(f"Downloading Foley: {remote_foley_path} -> {local_foley_path}")
    
    scp_result = subprocess.run(scp_cmd, capture_output=True, text=True)
    if scp_result.returncode == 0:
        logger.success(f"Successfully downloaded Foley to: {local_foley_path}")
        return local_foley_path
    else:
        logger.error(f"Failed to download Foley: {scp_result.stderr}")
        return None

if __name__ == "__main__":
    load_dotenv()
    
    # 1. ALWAYS free memory first if ComfyUI was recently used
    free_comfy_memory()
    
    # 2. Test with a known generated video
    test_video = "ComfyUI_00010_.mp4" 
    test_prompt = "A close-up of a vintage typewriter in a dusty office, cinematic lighting, 4k."
    
    result_path = run_remote_foley(
        remote_filename=test_video,
        prompt=test_prompt,
        scene_id=1
    )
    
    if result_path:
        print(f"\n✅ Foley Test Success: {result_path}")
    else:
        print(f"\n❌ Foley Test Failed.")
