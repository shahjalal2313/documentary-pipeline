# modules/06_assembly.py
import json
import os
from loguru import logger

# MoviePy 1.x to 2.x Compatibility Bridge
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeAudioClip,
        concatenate_videoclips
    )
except ImportError:
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeAudioClip,
        concatenate_videoclips
    )
    from moviepy.video.fx import Loop as video_loop
    from moviepy.audio.fx import AudioLoop as audio_loop
    
    # Patch VideoFileClip with MoviePy 1.x methods
    VideoFileClip.loop = lambda self, duration: self.with_effects([video_loop(duration=duration)])
    if not hasattr(VideoFileClip, "subclip"):
        VideoFileClip.subclip = lambda self, t_start, t_end: self.subclipped(t_start, t_end)
    if not hasattr(VideoFileClip, "set_audio"):
        VideoFileClip.set_audio = lambda self, audio: self.with_audio(audio)
    if not hasattr(VideoFileClip, "without_audio"):
        VideoFileClip.without_audio = lambda self: self.with_audio(None)
    
    # Patch AudioFileClip with MoviePy 1.x methods
    AudioFileClip.volumex = lambda self, factor: self.with_volume_scaled(factor)
    AudioFileClip.loop = lambda self, duration: self.with_effects([audio_loop(duration=duration)])

def build_rough_cut(
    clip_paths: list,
    narration_paths: list,
    foley_paths: list,
    output_path: str
) -> dict:
    """
    Assemble rough cut from AI clips + narration + foley.
    Returns timeline_data dict for Editing Assistant.
    Music intentionally excluded — added manually in DaVinci.
    """

    timeline_data = {"scenes": [], "total_duration": 0}
    assembled_clips = []
    current_time = 0.0

    # FIX 5: Use range() instead of zip() — prevents silent data loss
    for i in range(len(narration_paths)):
        clip_path = clip_paths[i]
        narration_path = narration_paths[i]
        foley_path = foley_paths[i] if i < len(foley_paths) else None

        # FIX 4: Error handling — skip corrupt/missing clips gracefully
        try:
            # ENSURE NO ECHO: Start by stripping any original audio from the clip
            video = VideoFileClip(clip_path).without_audio()
            narr_audio = AudioFileClip(narration_path)
        except Exception as e:
            logger.error(f"Scene {i+1} | Clip load FAILED: {clip_path} — {e}")
            continue

        try:
            # Narration is ground truth for duration
            duration = narr_audio.duration

            # Trim or loop video to match narration
            video = (
                video.loop(duration=duration)
                if video.duration < duration
                else video.subclip(0, duration)
            )

            # FIX 2: Loop foley to match narration duration (prevents cutoff)
            if foley_path:
                foley_audio = AudioFileClip(foley_path).volumex(0.25)
                foley_audio = foley_audio.loop(duration=duration)
                mixed_audio = CompositeAudioClip([narr_audio, foley_audio])
            else:
                mixed_audio = narr_audio

            video = video.set_audio(mixed_audio)
            assembled_clips.append(video)

            # Record scene to timeline JSON
            timeline_data["scenes"].append({
                "scene_id": i + 1,
                "start": round(current_time, 3),
                "end": round(current_time + duration, 3),
                "duration": round(duration, 3),
                "clip_path": clip_path,
                "narration_path": narration_path,
                "foley_path": foley_path,
            })
            current_time += duration

        except Exception as e:
            logger.error(f"Scene {i+1} | Assembly FAILED: {e}")

    if not assembled_clips:
        raise RuntimeError("No clips assembled — check logs for errors")

    # FIX 1: FPS from first clip instead of hardcoded 24
    output_fps = assembled_clips[0].fps or 24

    # Concatenate all scenes (using "chain" to prevent audio layering bugs)
    final = concatenate_videoclips(assembled_clips, method="chain")

    # Export rough cut
    final.write_videofile(
        output_path,
        fps=output_fps,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    # FIX 3: Close final composite
    final.close()
    for clip in assembled_clips:
        clip.close()

    # Export timeline JSON for Editing Assistant
    timeline_data["total_duration"] = round(current_time, 3)
    timeline_data["scene_count"] = len(timeline_data["scenes"])
    json_path = output_path.replace(".mp4", "_timeline.json")
    with open(json_path, "w") as f:
        json.dump(timeline_data, f, indent=2)

    logger.success(f"Rough cut complete: {output_path}")
    return timeline_data
