import os
import sys
import json
import requests
import importlib.util
import time
from loguru import logger
from dotenv import load_dotenv

# Project configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load main video module
video_mod = load_module("mod04", "modules/04_video.py")

def check_comfy_connection():
    """Verify ComfyUI is responding at the proxy URL."""
    try:
        url = video_mod.COMFYUI_URL
        logger.info(f"Checking ComfyUI at {url}...")
        response = requests.get(f"{url}/system_stats", timeout=15)
        if response.status_code == 200:
            logger.success("ComfyUI Connection Verified.")
            return True
        logger.error(f"ComfyUI returned status code {response.status_code}")
    except Exception as e:
        logger.error(f"ComfyUI Connection Failed: {e}")
    return False

def test_scene_generation():
    load_dotenv()
    os.makedirs(os.path.join(PROJECT_ROOT, "output", "clips"), exist_ok=True)
    
    if not check_comfy_connection():
        logger.error("ComfyUI service is not reachable. Ensure ComfyUI is running on port 8188.")
        return

    scenes = [
        {"id": 1, "prompt": "A close-up of a vintage typewriter in a dusty office, cinematic lighting, 4k."},
        {"id": 2, "prompt": "A futuristic neon city in the rain, cyberpunk style, drone shot, 4k."}
    ]
    
    results = []
    
    for scene in scenes:
        try:
            logger.info(f"--- Processing Scene {scene['id']} ---")
            
            # 1. Generate Video
            # mod04.generate_one_clip returns (local_path, remote_filename)
            video_path, remote_filename = video_mod.generate_one_clip(
                prompt=scene["prompt"],
                model="wan2",
                scene_id=scene["id"],
                topic_slug="verify"
            )
            
            results.append({"id": scene["id"], "video": video_path, "remote": remote_filename})
            logger.success(f"Scene {scene['id']} generated: {video_path} (Remote: {remote_filename})")
            
        except Exception as e:
            logger.error(f"Generation failed for scene {scene['id']}: {e}")

    if results:
        logger.success(f"Successfully generated {len(results)} scenes. Check output/clips for results.")

if __name__ == "__main__":
    test_scene_generation()
