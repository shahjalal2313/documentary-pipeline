# modules/03_voice.py
# NOTE: This module runs on the RunPod GPU pod, not your local machine.
# Call it via SSH or include in the RunPod worker script.
import os
import subprocess
from pathlib import Path
from loguru import logger

def get_audio_duration(audio_path: str) -> float:
    """Get exact audio duration using ffprobe."""
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

def generate_chapter_audio(text: str, output_path: str,
                            speed: float = 0.92) -> dict:
    """
    Generate voiceover for one chapter.
    speed=0.92 = slightly slower = more authoritative
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        from chatterbox.tts import ChatterboxTTS
        import torchaudio
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = ChatterboxTTS.from_pretrained(device)
        wav = model.generate(text)
        torchaudio.save(output_path, wav, model.sr)
        duration = get_audio_duration(output_path)
        logger.success(f"Audio generated: {output_path} ({duration:.1f}s)")
        return {"path": output_path, "duration": duration, "success": True}
    except Exception as e:
        logger.error(f"Chatterbox failed: {e}")
        return {"path": None, "duration": 0, "success": False, "error": str(e)}

def generate_all_chapters(chapters: list, topic_slug: str) -> list:
    """Generate voiceover for all chapters. Returns chapters with audio info."""
    results = []
    for ch in chapters:
        output_path = f"output/audio/{topic_slug}_ch{ch['chapter_id']:02d}.wav"
        audio_info = generate_chapter_audio(ch["narration"], output_path)
        results.append({**ch, **audio_info})
        logger.info(f"Chapter {ch['chapter_id']} ({ch['name']}): {audio_info['duration']:.1f}s")
    return results

if __name__ == "__main__":
    test_text = "In 2001, Enron was worth seventy billion dollars. Eighteen months later, it was gone. Twenty thousand families lost everything. This is the story of the biggest corporate fraud in American history."
    result = generate_chapter_audio(test_text, "output/audio/test_chapter.wav")
    print(f"Duration: {result['duration']:.1f}s")
    print(f"File: {result['path']}")
