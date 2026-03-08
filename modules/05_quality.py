# modules/05_quality.py
import cv2
import numpy as np
import subprocess
from pathlib import Path
from loguru import logger
from config.settings import Config

def measure_sharpness(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    scores = []
    for i in [int(total * x) for x in [0.2, 0.4, 0.6, 0.8]]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            scores.append(cv2.Laplacian(gray, cv2.CV_64F).var())
    cap.release()
    return float(np.mean(scores)) if scores else 0

def measure_motion(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    ret, prev = cap.read()
    if not ret:
        return 0
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    scores = []
    for _ in range(8):
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        scores.append(float(np.mean(mag)))
        prev_gray = gray
    cap.release()
    return min(float(np.mean(scores)) / 10.0, 1.0) if scores else 0

def get_duration(video_path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 0

def passes_quality_gate(video_path: str) -> tuple:
    metrics = {
        "sharpness": measure_sharpness(video_path),
        "motion":    measure_motion(video_path),
        "duration":  get_duration(video_path)
    }
    passed = (
        metrics["sharpness"] >= Config.MIN_SHARPNESS_SCORE and
        metrics["motion"]    <= Config.MAX_MOTION_SCORE and
        metrics["duration"]  >= Config.MIN_CLIP_DURATION
    )
    return passed, metrics

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "output/clips/test_scene001.mp4"
    passed, metrics = passes_quality_gate(path)
    print(f"File: {path}")
    print(f"Sharpness: {metrics['sharpness']:.1f} (min: {Config.MIN_SHARPNESS_SCORE})")
    print(f"Motion: {metrics['motion']:.3f} (max: {Config.MAX_MOTION_SCORE})")
    print(f"Duration: {metrics['duration']:.1f}s (min: {Config.MIN_CLIP_DURATION})")
    print(f"Result: {'\u2705 PASSED' if passed else '\u274c FAILED'}")
