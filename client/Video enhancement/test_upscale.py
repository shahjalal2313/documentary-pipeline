import subprocess
import os
from loguru import logger

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

if __name__ == "__main__":
    # Test paths - adjust these if needed when running on the pod
    test_input = "test_input.mp4"
    test_output = "test_output_upscaled.mp4"
    
    if os.path.exists(test_input):
        upscale_clip(test_input, test_output)
    else:
        logger.warning(f"Test input file not found: {test_input}. Please provide a 720p mp4 to test.")
