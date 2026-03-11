import os
import sys
from loguru import logger
from modules_foley import generate_foley_for_clip, FOLEY_CMD_TEMPLATE

# Update config for pod paths
import modules_foley
modules_foley.FOLEY_DIR = '/workspace/HunyuanVideo-Foley'
modules_foley.OUTPUT_DIR = '/workspace/output/foley'
modules_foley.SILENCE_PLACEHOLDER = '/workspace/assets/silence.wav'

# Updated path
test_clip = "/workspace/HunyuanVideo-Foley/assets/MovieGenAudioBenchSfx/video_with_audio/0.mp4"

modules_foley.FOLEY_CMD_TEMPLATE = [
    "python3", "infer.py",
    "--model_path", "pretrained_models",
    "--single_video", "{video}",
    "--output_dir", "/workspace/output/foley_temp",
    "--enable_offload"
]

def test():
    if not os.path.exists(test_clip):
        logger.error(f"Test clip not found at {test_clip}")
        return

    logger.info("Testing FOLEY profile...")
    try:
        os.makedirs("/workspace/output/foley_temp", exist_ok=True)
        # Note: generate_foley_for_clip will fail if infer.py doesn't produce the exact output_path it expects
        # We might need to adjust the logic to look in the output_dir
        res = generate_foley_for_clip(test_clip, 1, sound_profile="foley")
        logger.success(f"Foley test result: {res}")
    except Exception as e:
        logger.error(f"Foley test failed: {e}")

    logger.info("Testing SILENT profile...")
    res_silent = generate_foley_for_clip(test_clip, 2, sound_profile="silent")
    logger.success(f"Silent test result: {res_silent}")

if __name__ == '__main__':
    test()
