# Use NVIDIA CUDA 12.8 base image for RTX 5090 (Blackwell) support
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/workspace/venv/bin:$PATH"

# 1. Install System Dependencies
RUN apt-get update && apt-get install -y \
    git git-lfs aria2 ffmpeg libgl1-mesa-glx libglib2.0-0 wget build-essential \
    python3.12 python3.12-venv python3.12-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up Workspace
WORKDIR /workspace

# 3. Create Virtual Environment
RUN python3.12 -m venv /workspace/venv
ENV VIRTUAL_ENV=/workspace/venv
RUN /workspace/venv/bin/pip install --upgrade pip setuptools wheel

# 4. Install PyTorch 2.8+ (Required for RTX 5090)
RUN /workspace/venv/bin/pip install "torch>=2.8.0" "torchaudio>=2.8.0" "torchvision>=0.19.0" --index-url https://download.pytorch.org/whl/cu128

# 5. Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI
WORKDIR /workspace/ComfyUI
RUN /workspace/venv/bin/pip install -r requirements.txt


# 5. Install Custom Nodes
WORKDIR /workspace/ComfyUI/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git && 
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && 
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && 
    git clone https://github.com/Kijai/ComfyUI-KJNodes.git

# 6. Install HunyuanVideo-Foley
WORKDIR /workspace
RUN git clone https://github.com/tencent/HunyuanVideo-Foley.git /workspace/HunyuanVideo-Foley
WORKDIR /workspace/HunyuanVideo-Foley
RUN /workspace/venv/bin/pip install torch torchaudio transformers librosa tqdm loguru torchcodec

# 7. Apply Specialized Optimizations
RUN /workspace/venv/bin/pip install "numpy==1.26.4" sageattention==2.2 chatterbox-tts
RUN /workspace/venv/bin/pip uninstall -y opencv-python opencv-python-headless && 
    /workspace/venv/bin/pip install "opencv-python<4.10" "opencv-python-headless<4.10"

# 8. Create the "Auto-Restorer" script inside the image
# (Note: We embed it here so the image is self-contained)
RUN echo '#!/bin/bash

set -e

echo "--- 📥 CHECKING MODELS (WAN 2.2 + FOLEY) ---"

mkdir -p /workspace/ComfyUI/models/diffusion_models

mkdir -p /workspace/ComfyUI/models/vae

mkdir -p /workspace/ComfyUI/models/text_encoders

mkdir -p /workspace/ComfyUI/models/loras

mkdir -p /workspace/HunyuanVideo-Foley/pretrained_models



declare -A models=(

    ["/workspace/ComfyUI/models/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"

    ["/workspace/ComfyUI/models/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"

    ["/workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors"

    ["/workspace/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

    ["/workspace/ComfyUI/models/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"

    ["/workspace/ComfyUI/models/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors"]="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors"

    ["/workspace/HunyuanVideo-Foley/pretrained_models/hunyuanvideo_foley.pth"]="https://huggingface.co/tencent/HunyuanVideo-Foley/resolve/main/hunyuanvideo_foley.pth"

)



for path in "${!models[@]}"; do

    if [ ! -f "$path" ]; then

        echo "Downloading $(basename "$path")..."

        aria2c -x 16 -s 16 -k 1M "${models[$path]}" -d $(dirname "$path") -o $(basename "$path")

    else

        echo "--- ✅ $(basename "$path") exists ---"

    fi

done' > /workspace/restore_models.sh && chmod +x /workspace/restore_models.sh

# 9. Startup Command
WORKDIR /workspace
CMD ["/bin/bash", "-c", "/workspace/restore_models.sh && cd /workspace/ComfyUI && python main.py --listen --port 8188"]
