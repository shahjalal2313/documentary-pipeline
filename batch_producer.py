import json
import os
import sys
import time
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add project root to path for module imports
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

import importlib.util
def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

video_mod = load_module_from_path("mod04", str(PROJECT_ROOT / "modules/04_video.py"))
generate_one_clip = video_mod.generate_one_clip

def run_batch_production(script_path: str, batch_size: int = 3, start_scene: int = 1):
    """
    Reads a script JSON and processes scenes in batches.
    """
    load_dotenv()
    
    script_path = Path(script_path)
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    topic_slug = script_path.stem
    scenes = data.get("scenes", [])
    
    total_scenes = len(scenes)
    logger.info(f"Loaded {total_scenes} scenes from {script_path.name}")
    
    # Filter scenes based on start_scene
    scenes_to_process = [s for s in scenes if s["scene_id"] >= start_scene]
    
    if not scenes_to_process:
        logger.warning(f"No scenes to process starting from ID {start_scene}")
        return

    # Process in batches
    for i in range(0, len(scenes_to_process), batch_size):
        batch = scenes_to_process[i : i + batch_size]
        batch_ids = [s["scene_id"] for s in batch]
        
        logger.info(f"--- Processing Batch: Scenes {batch_ids} ---")
        
        for scene in batch:
            scene_id = scene["scene_id"]
            prompt = scene.get("comfyui_prompt")
            model = scene.get("model", "wan2")
            
            # Check if file already exists to avoid redundant generation
            output_file = PROJECT_ROOT / f"output/clips/{topic_slug}_scene{scene_id:03d}.mp4"
            if output_file.exists():
                logger.info(f"Scene {scene_id} already exists at {output_file}. Skipping.")
                continue

            try:
                logger.info(f"Generating Scene {scene_id}...")
                video_path, remote_name = generate_one_clip(
                    prompt=prompt,
                    model=model,
                    scene_id=scene_id,
                    topic_slug=topic_slug,
                    duration_sec=scene.get("duration_sec", 5.0)
                )
                logger.success(f"Successfully generated Scene {scene_id}: {video_path}")
            except Exception as e:
                logger.error(f"Failed to generate Scene {scene_id}: {e}")
                logger.info("Stopping batch due to error to prevent credit waste.")
                return

        if i + batch_size < len(scenes_to_process):
            logger.info(f"Batch complete. Waiting 10 seconds before next batch...")
            time.sleep(10)
        else:
            logger.success("All requested scenes processed!")

if __name__ == "__main__":
    # Example usage:
    # python batch_producer.py output/scripts/the_rise_and_fall_of_wework.json 3 1
    
    if len(sys.argv) < 2:
        print("Usage: python batch_producer.py <script_json_path> [batch_size] [start_scene_id]")
        sys.exit(1)
        
    script_file = sys.argv[1]
    b_size = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    s_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    run_batch_production(script_file, b_size, s_id)
