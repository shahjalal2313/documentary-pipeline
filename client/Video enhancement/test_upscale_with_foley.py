import os
from loguru import logger

# MoviePy 1.x to 2.x Compatibility Bridge
try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip

def merge_video_audio(video_path, audio_path, output_path):
    """
    Precisely merges an upscaled video clip with a foley audio file.
    Replaces any existing audio in the video with the new audio.
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return

    try:
        logger.info(f"Merging {os.path.basename(video_path)} with {os.path.basename(audio_path)}...")
        
        # Load video and audio
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # Match durations precisely
        common_duration = min(video.duration, audio.duration)
        logger.info(f"Duration: Video {video.duration:.2f}s, Audio {audio.duration:.2f}s -> Target {common_duration:.2f}s")

        # Trim both to the common duration
        if hasattr(video, "subclipped"):
            video = video.subclipped(0, common_duration)
            final_audio = audio.subclipped(0, common_duration)
        else:
            video = video.subclip(0, common_duration)
            final_audio = audio.subclip(0, common_duration)
        
        # Set the audio to the video
        if hasattr(video, "with_audio"):
            final_clip = video.with_audio(final_audio)
        else:
            final_clip = video.set_audio(final_audio)

        # Write result
        logger.info(f"Exporting merged file to {output_path}...")
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            fps=video.fps or 24
        )

        # Cleanup
        video.close()
        audio.close()
        final_clip.close()
        
        logger.success(f"Successfully assembled: {output_path}")

    except Exception as e:
        logger.error(f"Assembly failed: {e}")

if __name__ == "__main__":
    # Define paths based on your request
    video_in = r"F:\YA Business\documentary-pipeline\output\clips\test_upscale_result.mp4"
    audio_in = r"F:\YA Business\documentary-pipeline\output\clips\scene_1_foley.wav"
    video_out = r"F:\YA Business\documentary-pipeline\output\clips\test_upscale_with_foley.mp4"

    merge_video_audio(video_in, audio_in, video_out)
