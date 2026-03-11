import sys
import os
from loguru import logger

# Add documentary-pipeline to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import using a hack since it starts with a number
import importlib
module_06 = importlib.import_module("modules.06_assembly")
build_rough_cut = module_06.build_rough_cut

def test_assembly():
    clip_path = 'f:/YA Business/documentary-pipeline/output/clips/test_discovery_scene001.mp4'
    narration_path = 'f:/YA Business/documentary-pipeline/output/audio/enron_test_ch01.wav'
    foley_path = 'f:/YA Business/documentary-pipeline/output/audio/final_rebirth_test.wav'
    output_path = 'f:/YA Business/documentary-pipeline/output/assembled/test_rough_cut.mp4'

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    clip_paths = [clip_path]
    narration_paths = [narration_path]
    foley_paths = [foley_path]

    logger.info("Starting test assembly...")
    try:
        timeline = build_rough_cut(clip_paths, narration_paths, foley_paths, output_path)
        logger.success("Test assembly completed!")
        logger.info(f"Timeline: {timeline}")
        
        # Verify files exist
        if os.path.exists(output_path):
            logger.success(f"Video created: {output_path}")
        else:
            logger.error(f"Video NOT created: {output_path}")

        json_path = output_path.replace(".mp4", "_timeline.json")
        if os.path.exists(json_path):
            logger.success(f"Timeline JSON created: {json_path}")
        else:
            logger.error(f"Timeline JSON NOT created: {json_path}")

    except Exception as e:
        logger.exception(f"Test assembly FAILED: {e}")

if __name__ == "__main__":
    test_assembly()
