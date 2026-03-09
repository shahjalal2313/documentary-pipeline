# modules/03b_foley.py
import subprocess
import os
from pathlib import Path
from loguru import logger

# ── Config block (change CLI args here if Tencent updates repo) ──────────────
FOLEY_DIR = "/workspace/HunyuanVideo-Foley"
OUTPUT_DIR = "output/foley"
SILENCE_PLACEHOLDER = "/workspace/assets/silence.wav"
INFERENCE_TIMEOUT = 600  # seconds — prevents pipeline hangs

FOLEY_CMD_TEMPLATE = [
    "python", "inference.py",
    "--video", "{video}",
    "--output", "{output}"
]
# ─────────────────────────────────────────────────────────────────────────────

def normalize_audio(audio_path: str, target_sr: int = 48000) -> str:
    """Normalize audio to 48kHz stereo using ffmpeg. Returns path."""
    normalized_path = audio_path.replace(".wav", "_norm.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-ar", str(target_sr),
        "-ac", "2",
        normalized_path
    ], capture_output=True, check=True)
    os.replace(normalized_path, audio_path)  # overwrite with normalized
    return audio_path

def trim_pad_audio(audio_path: str, target_duration: float) -> str:
    """Trim or pad audio to exactly match video duration."""
    trimmed_path = audio_path.replace(".wav", "_aligned.wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-t", str(target_duration),  # trim to duration
        "-af", f"apad=pad_dur={target_duration}",  # pad if too short
        trimmed_path
    ], capture_output=True, check=True)
    os.replace(trimmed_path, audio_path)
    return audio_path

def get_video_duration(clip_path: str) -> float:
    """Get exact video duration in seconds using ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        clip_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

def get_silence_placeholder(duration: float) -> str:
    """Generate a silence WAV of exact duration."""
    out = f"{OUTPUT_DIR}/silence_{duration:.2f}s.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=48000:cl=stereo",
        "-t", str(duration), out
    ], capture_output=True)
    return out

def generate_foley_for_clip(
    clip_path: str,
    scene_id: int,
    sound_profile: str = "foley"
) -> str:
    """
    Generate foley audio for one video clip.
    Returns path to audio file (foley or silence placeholder).
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    video_duration = get_video_duration(clip_path)
    output_path = f"{OUTPUT_DIR}/scene_{scene_id:02d}_foley.wav"

    # ── Scene filter: skip Foley for silent/music_only profiles ──────────────
    if sound_profile in ("silent", "music_only"):
        logger.info(f"Scene {scene_id} | Profile: {sound_profile} → silence placeholder")
        return get_silence_placeholder(video_duration)

    # ── Build CLI command from config block ───────────────────────────────────
    cmd = [
        part.replace("{video}", clip_path).replace("{output}", output_path)
        for part in FOLEY_CMD_TEMPLATE
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=INFERENCE_TIMEOUT,  # prevents pipeline hang
            cwd=FOLEY_DIR
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        # ── Post-processing: normalize + align duration ───────────────────────
        normalize_audio(output_path, target_sr=48000)
        trim_pad_audio(output_path, video_duration)

        logger.success(
            f"Scene {scene_id} | Clip: {Path(clip_path).name} | "
            f"Foley: {Path(output_path).name} ({video_duration:.1f}s)"
        )
        return output_path

    except subprocess.TimeoutExpired:
        logger.warning(f"Scene {scene_id} | Foley TIMEOUT after {INFERENCE_TIMEOUT}s → silence fallback")
        return get_silence_placeholder(video_duration)

    except Exception as e:
        logger.warning(f"Scene {scene_id} | Foley FAILED: {e} → silence fallback")
        return get_silence_placeholder(video_duration)

def generate_all_foley(clip_paths: list, scenes: list) -> list:
    """
    Process all clips. Returns list of audio paths (never None).
    scenes: list of scene dicts with 'sound_profile' key.
    """
    paths = []
    for i, (clip, scene) in enumerate(zip(clip_paths, scenes)):
        profile = scene.get("sound_profile", "foley")
        path = generate_foley_for_clip(clip, i + 1, sound_profile=profile)
        paths.append(path)

    foley_count = sum(1 for s in scenes if s.get("sound_profile", "foley") not in ("silent", "music_only"))
    logger.info(
        f"Foley complete: {foley_count} generated, "
        f"{len(paths) - foley_count} silence placeholders"
    )
    return paths
