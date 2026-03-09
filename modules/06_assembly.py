# modules/06_assembly.py
import subprocess
import os
from pathlib import Path
from loguru import logger

BGM_TRACKS = {
    "tense":    "luts/bgm_tense.mp3",
    "minimal":  "luts/bgm_minimal.mp3",
    "dramatic": "luts/bgm_dramatic.mp3"
}

def assemble_video_moviepy(scenes: list, audio_chapters: list,
                            output_path: str, bgm_mood: str = "tense") -> str:
    """
    Assemble final video using MoviePy.
    scenes: list of dicts with 'clip_path' and 'duration_sec'
    audio_chapters: list of dicts with 'path' and 'duration'
    """
    # Using MoviePy 2.x API for Python 3.13 compatibility
    try:
        from moviepy import (
            VideoFileClip, AudioFileClip, concatenate_videoclips,
            concatenate_audioclips, CompositeAudioClip
        )
    except ImportError:
        # Fallback for MoviePy 1.x
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, concatenate_videoclips,
            concatenate_audioclips, CompositeAudioClip
        )

    logger.info("Loading video clips...")
    clips = []
    for s in scenes:
        if s.get("clip_path") and Path(s["clip_path"]).exists():
            clip = VideoFileClip(s["clip_path"])
            clips.append(clip)
        else:
            logger.warning(f"Missing clip: {s.get('clip_path')}")

    if not clips:
        raise ValueError("No valid clips found")

    logger.info(f"Concatenating {len(clips)} clips...")
    video = concatenate_videoclips(clips, method="compose")

    logger.info("Loading audio chapters...")
    voice_clips = []
    for ch in audio_chapters:
        if ch.get("path") and Path(ch["path"]).exists():
            voice_clips.append(AudioFileClip(ch["path"]))

    if voice_clips:
        voice = concatenate_audioclips(voice_clips)
        # subclip -> subclipped in v2
        if hasattr(voice, 'subclipped'):
            voice = voice.subclipped(0, min(voice.duration, video.duration))
        else:
            voice = voice.subclip(0, min(voice.duration, video.duration))
    else:
        voice = None

    # Add background music (ducked under voice)
    bgm_path = BGM_TRACKS.get(bgm_mood, BGM_TRACKS["tense"])
    if Path(bgm_path).exists():
        bgm = AudioFileClip(bgm_path)
        # volumex -> with_volume_scaled in v2
        if hasattr(bgm, 'with_volume_scaled'):
            bgm = bgm.with_volume_scaled(0.08)
        else:
            bgm = bgm.volumex(0.08)
        
        # subclip -> subclipped in v2
        if hasattr(bgm, 'subclipped'):
            bgm = bgm.subclipped(0, min(bgm.duration, video.duration))
        else:
            bgm = bgm.subclip(0, min(bgm.duration, video.duration))
            
        if voice:
            final_audio = CompositeAudioClip([voice, bgm])
        else:
            final_audio = bgm
    else:
        final_audio = voice
        logger.warning(f"BGM not found: {bgm_path}")

    if final_audio:
        # set_audio -> with_audio in v2
        if hasattr(video, 'with_audio'):
            video = video.with_audio(final_audio)
        else:
            video = video.set_audio(final_audio)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Rendering final video: {output_path}")
    
    # write_videofile arguments changed in v2 (verbose and logger handled differently)
    video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="slow"
    )
    logger.success(f"Assembly complete: {output_path}")
    return output_path

if __name__ == "__main__":
    # Test with whatever clips you have
    import glob
    clip_files = sorted(glob.glob("output/clips/*.mp4"))[:5]
    audio_files = sorted(glob.glob("output/audio/*.wav"))[:2]

    if not clip_files:
        print("❌ No clips found in output/clips/ - run Module 4 first")
        exit(1)

    scenes = [{"clip_path": f} for f in clip_files]
    chapters = [{"path": f} for f in audio_files]

    result = assemble_video_moviepy(scenes, chapters, "output/assembled/test_assembly.mp4")
    print(f"\n✅ Test assembly complete: {result}")
