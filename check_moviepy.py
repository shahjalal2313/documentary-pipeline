import moviepy
print(f"MoviePy version: {moviepy.__version__}")
try:
    import moviepy.editor
    print("moviepy.editor imported successfully")
except ImportError as e:
    print(f"moviepy.editor import failed: {e}")

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    print("VideoFileClip imported from moviepy.video.io.VideoFileClip")
except ImportError as e:
    print(f"VideoFileClip import failed: {e}")
