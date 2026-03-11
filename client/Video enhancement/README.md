# AI Video Upscaling (Real-ESRGAN)

This module handles the high-quality upscaling of AI-generated clips. Because Wan 2.2 is generated at 720p to avoid VRAM limits, we use **Real-ESRGAN x4plus** to upscale the final clips to **1440p (2K)**.

## How it Works
The `test_upscale.py` script triggers a subprocess on the RunPod that calls the Real-ESRGAN inference engine.
- **Input:** 720p (1280x720) MP4
- **Output:** 1440p (2560x1440) MP4
- **Scale:** 2.0x
- **Performance:** ~9 seconds of processing per 1 second of video (on RTX 4090).

## Environment Requirements
This script **must** be run on the RunPod with the following setup:
1. **GPU:** RTX 4090 (24GB VRAM).
2. **Path:** Real-ESRGAN repository cloned at `/workspace/Real-ESRGAN/`.
3. **Environment:** Python environment at `/workspace/venv_persistent/`.

### Critical Patches Applied
The following fixes were applied to the pod to make this work:
- **BasicSR Fix:** Patched `basicsr/data/degradations.py` to fix `torchvision` compatibility.
- **Dependencies:** Installed `ffmpeg-python` in the persistent venv.

## Usage Instructions

### 1. Upload to Pod
From your local Windows terminal:
```powershell
scp -P [PORT] "F:\YA Business\documentary-pipeline\client\Video enhancement	est_upscale.py" root@[IP]:/workspace/test_upscale.py
scp -P [PORT] "path/to/your/video.mp4" root@[IP]:/workspace/test_input.mp4
```

### 2. Run Upscale
Connect via SSH and run:
```bash
cd /workspace
/workspace/venv_persistent/bin/python3 test_upscale.py
```

### 3. Download Result
From your local Windows terminal:
```powershell
scp -P [PORT] root@[IP]:/workspace/test_output_upscaled.mp4/test_input_out.mp4 "F:\YA Business\documentary-pipeline\output\clips\upscaled_result.mp4"
```
*Note: Real-ESRGAN creates a directory for the output; the actual video file is inside it.*

## Files in this Directory
- `test_upscale.py`: The core upscaling script for the pod.
- `test_upscale_with_foley.py`: Local script to merge upscaled video with high-fidelity foley audio.
