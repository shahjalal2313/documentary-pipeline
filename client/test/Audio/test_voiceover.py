import os
import sys
import json
import subprocess
import requests
import time
from loguru import logger
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[2] 
load_dotenv(PROJECT_ROOT / ".env")

# Pod configuration
POD_ID = "io253g0p0ilb70"
POD_IP = "203.57.40.62"
POD_PORT = "10093"
COMFYUI_URL = f"https://{POD_ID}-8188.proxy.runpod.net"

def free_comfy_memory():
    """Request ComfyUI to unload models and free GPU memory."""
    try:
        logger.info("Requesting ComfyUI to free memory...")
        requests.post(f"{COMFYUI_URL}/free", json={"unload_models": True, "free_memory": True}, timeout=15)
        logger.success("GPU memory cleared.")
    except Exception as e:
        logger.warning(f"Could not reach ComfyUI to free memory: {e}")

def generate_full_narrative_remote(chapters, output_filename):
    """
    Sends all chapters to the pod for high-quality sentence-by-sentence generation.
    """
    remote_script_path = "/workspace/voice_gen_full_pro.py"
    remote_data_path = "/workspace/voice_chapters.json"
    remote_output_path = f"/workspace/output/audio/{output_filename}"
    
    # Clean chapters
    cleaned_chapters = []
    for ch in chapters:
        text = ch["narration"].replace("\n", " ")
        cleaned_chapters.append({"id": ch["chapter_id"], "text": text})

    # 1. Upload Data JSON
    local_data_file = PROJECT_ROOT / "temp_chapters.json"
    with open(local_data_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_chapters, f, indent=2)
    
    logger.info("Uploading chapter data...")
    subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-P", POD_PORT, str(local_data_file), f"root@{POD_IP}:{remote_data_path}"], check=True)
    os.remove(local_data_file)

    # 2. Create Pro Helper Script
    helper_content = f"""
import sys
import json
import re
from unittest.mock import MagicMock
from pathlib import Path
import torch
import torchaudio
import numpy as np
import pyloudnorm as ffn

# --- Patching ---
class PassthroughMock:
    def apply_watermark(self, wav, sample_rate=None): return wav
dummy_perth = MagicMock()
dummy_perth.PerthImplicitWatermarker = PassthroughMock
sys.modules['perth'] = dummy_perth

from chatterbox.tts import ChatterboxTTS

def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if s.strip()]

def main():
    with open('{remote_data_path}', 'r') as f:
        chapters = json.load(f)
    
    output_path = "{remote_output_path}"
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Chatterbox on {{device}}...")
    model = ChatterboxTTS.from_pretrained(device)
    sr = model.sr
    
    all_audio_segments = []
    sentence_gap = torch.zeros(1, int(sr * 0.30))
    chapter_gap = torch.zeros(1, int(sr * 1.20))
    
    for ch in chapters:
        print(f"--- Processing Chapter {{ch['id']}} ---")
        sentences = split_into_sentences(ch['text'])
        
        for i, sent in enumerate(sentences):
            print(f"  Sent {{i+1}}/{{len(sentences)}}: {{sent[:40]}}...")
            wav = model.generate(sent)
            all_audio_segments.append(wav)
            all_audio_segments.append(sentence_gap)
        
        all_audio_segments.append(chapter_gap)

    print("Stitching audio together...")
    full_wav = torch.cat(all_audio_segments, dim=1)
    
    # Normalization using pyloudnorm
    wav_np = full_wav.cpu().numpy().T # [T, 1]
    meter = ffn.Meter(sr)
    # Correct pyloudnorm API is integrated_loudness
    loudness = meter.integrated_loudness(wav_np)
    
    print(f"Current Loudness: {{loudness:.2f}} LUFS. Normalizing to -14.0...")
    normalized_wav = ffn.normalize.loudness(wav_np, loudness, -14.0)
    
    final_tensor = torch.from_numpy(normalized_wav.T).float()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(output_path, final_tensor, sr)
    print(f"SUCCESS: Final narration saved to {{output_path}}")

if __name__ == '__main__':
    main()
"""
    
    local_temp_script = PROJECT_ROOT / "temp_full_voice_helper.py"
    with open(local_temp_script, "w", encoding="utf-8") as f:
        f.write(helper_content)
        
    logger.info("Uploading Pro Voice Generation helper...")
    subprocess.run(["scp", "-o", "StrictHostKeyChecking=no", "-P", POD_PORT, str(local_temp_script), f"root@{POD_IP}:{remote_script_path}"], check=True)
    os.remove(local_temp_script)

    # 3. Execute
    logger.info("Starting Full Script Generation (this will take ~5-10 minutes)...")
    python_cmd = f"source /workspace/venv_persistent/bin/activate && python3 {remote_script_path}"
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", POD_PORT, f"root@{POD_IP}", python_cmd]
    
    start_time = time.time()
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        logger.error(f"Generation failed: {result.stderr}")
        return None
    
    logger.success(f"Full narration generated in {duration:.1f}s")
    
    # 4. Download
    local_path = PROJECT_ROOT / "output" / "audio" / output_filename
    scp_down_cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-P", POD_PORT, f"root@{POD_IP}:{remote_output_path}", str(local_path)]
    subprocess.run(scp_down_cmd, check=True)
    
    logger.success(f"FINAL AUDIO DOWNLOADED: {local_path}")
    return str(local_path)

def test_full_script_voiceover():
    script_path = PROJECT_ROOT / "output" / "scripts" / "the_rise_and_fall_of_wework.json"
    
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
        
        chapters = script_data["chapters"]
        free_comfy_memory()
        generate_full_narrative_remote(chapters, "full_wework_narration_pro.wav")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_full_script_voiceover()
