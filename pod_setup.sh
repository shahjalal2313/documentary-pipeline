#!/bin/bash
# pod_setup.sh - Run this on a NEW RunPod to restore the environment

echo "--- Starting Surgical Installation for Python 3.12 ---"

# 1. Update tools
pip install --upgrade pip setuptools wheel

# 2. Bridge Numpy (for Python 3.12 compatibility)
pip install "numpy==1.26.4"

# 3. Isolated Chatterbox Install
pip install chatterbox-tts --no-deps

# 4. Manual dependency installation
pip install torch torchaudio transformers librosa tqdm requests loguru torchcodec conformer==0.3.2 diffusers==0.29.0 gradio==5.44.1 omegaconf pykakasi==2.3.0 pyloudnorm resemble-perth==1.0.1 s3tokenizer spacy-pkuseg safetensors==0.5.3 transformers==4.46.3

# 5. Fix OpenCV
pip uninstall -y opencv-python opencv-python-headless
pip install "opencv-python<4.10" "opencv-python-headless<4.10"

# 6. Verify
python3 -c "import numpy; import cv2; from chatterbox.tts import ChatterboxTTS; print('--- SUCCESS: Environment Restored ---')"
