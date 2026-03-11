# Professional Voiceover Generation Test

This directory contains `test_voiceover.py`, a high-fidelity test script designed for long-form documentary narration (8-12+ minutes).

## Overview

The `test_voiceover.py` script automates the generation of a complete voiceover from a JSON script. It leverages the GPU power of an active RunPod while ensuring the highest possible audio quality through advanced processing techniques.

## Key Features

- **Script-Based Input:** Automatically reads chapters and narration text from your project's JSON scripts (e.g., `the_rise_and_fall_of_wework.json`).
- **Sentence-by-Sentence Processing:** Splits long narration into individual sentences before generation. This prevents the AI from becoming distorted or losing energy over long durations.
- **Natural Pacing:** 
  - Adds a **300ms silence** between sentences.
  - Adds a **1.2s silence** between chapters.- **Loudness Normalization:** Uses `pyloudnorm` to standardize the final output to **-14.0 LUFS** (the global standard for YouTube and streaming), ensuring clear and consistent volume.
- **Memory Management:** Automatically sends a "free memory" request to the ComfyUI API on the pod before starting, preventing "Out of Memory" (OOM) errors.
- **Remote Execution:** Orchestrates the entire process in the cloud and automatically downloads the finished `.wav` file to your local `output/audio/` folder.

## Prerequisites

1. **Active RunPod:** Ensure your pod is running and accessible via SSH.
2. **Configuration:** Verify that `POD_ID`, `POD_IP`, and `POD_PORT` in the script match your current active pod.
3. **Environment:** The script uses the local `venv` for orchestration (requires `requests`, `loguru`, and `python-dotenv`).

## How to Use

1. **Prepare Script:** Ensure your target JSON script exists in `documentary-pipeline/output/scripts/`.
2. **Run Test:**
   ```powershell
   .\venv\Scripts\python.exe client	est\Audio	est_voiceover.py
   ```
3. **Wait:** The process typically takes 5–10 minutes for a full documentary script.
4. **Retrieve Output:** Find your final high-quality narration at:
   `documentary-pipeline/output/audio/full_wework_narration_pro.wav`

## Advanced Customization

You can modify the following parameters inside `test_voiceover.py` to adjust the pacing:

### Pacing Presets

| Preset | Sentence Gap | Chapter Gap | Use Case |
| :--- | :--- | :--- | :--- |
| **Deliberate (Current)** | `0.30s` | `1.20s` | High-focus documentaries, complex topics |
| **Fast (Previous)** | `0.15s` | `0.70s` | Quick-paced reels, highlights, fast narrations |

- `loudness target`: Change from `-14.0` if a different LUFS standard is required.

