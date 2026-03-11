import os
import sys
import json
import importlib.util
from loguru import logger
from dotenv import load_dotenv

# Add project root to path for module imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import numbered modules using importlib
video_mod = load_module_from_path("mod04", os.path.join(PROJECT_ROOT, "modules", "04_video.py"))
foley_mod = load_module_from_path("mod03b", os.path.join(PROJECT_ROOT, "modules", "03b_foley.py"))

generate_one_clip = video_mod.generate_one_clip
generate_foley_for_clip = foley_mod.generate_foley_for_clip

def run_test_pipeline():
    """
    Test script to:
    1. Generate 2 video clips using Wan 2.2 via RunPod/ComfyUI.
    2. Generate Foley audio for each clip.
    3. Output final clips (video + foley) in the clips folder.
    """
    load_dotenv()
    
    # Mock script data for 2 scenes
    scenes = [
        {
            "id": 1,
            "visual_prompt": "A cinematic close-up of a vintage typewriter's keys striking paper in a dimly lit 1940s office, dust motes dancing in a single beam of light, 4k, highly detailed.",
            "sound_profile": "foley",
            "topic_slug": "test_verification"
        },
        {
            "id": 2,
            "visual_prompt": "An expansive drone shot of a futuristic neon city during a heavy rainstorm at night, flying cars moving between skyscrapers, cyberpunk aesthetic, vibrant colors.",
            "sound_profile": "foley",
            "topic_slug": "test_verification"
        }
    ]

    logger.info("Starting verification test: 2 Scenes (Video + Foley)")
    
    generated_results = []

    for scene in scenes:
        scene_id = scene["id"]
        logger.info(f"--- Processing Scene {scene_id} ---")
        
        try:
            # 1. Generate Video Clip
            video_path = generate_one_clip(
                prompt=scene["visual_prompt"],
                model="wan2",
                scene_id=scene_id,
                topic_slug=scene["topic_slug"]
            )
            
            # 2. Generate Foley (Note: This is designed for Pod use, may fallback to silence if local)
            foley_path = generate_foley_for_clip(
                clip_path=video_path,
                scene_id=scene_id,
                sound_profile=scene["sound_profile"]
            )
            
            generated_results.append({
                "scene_id": scene_id,
                "video": video_path,
                "foley": foley_path
            })
            
        except Exception as e:
            logger.error(f"Failed to process Scene {scene_id}: {e}")
            log_issue(scene_id, str(e))

    logger.success("Verification test completed.")
    for res in generated_results:
        logger.info(f"Scene {res['scene_id']}: Video={res['video']}, Foley={res['foley']}")

def log_issue(scene_id, error_msg):
    log_dir = os.path.join("Review", "Phase 3")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "Verification_Issues.md")
    
    with open(log_file, "a") as f:
        f.write(f"## Issue in Scene {scene_id}\n")
        f.write(f"- **Error:** {error_msg}\n")
        f.write(f"- **Timestamp:** {json.dumps(str(logger))}\n\n")

if __name__ == "__main__":
    run_test_pipeline()
