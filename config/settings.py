import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY")
    RUNPOD_API_KEY         = os.getenv("RUNPOD_API_KEY")
    RUNPOD_ENDPOINT_ID     = os.getenv("RUNPOD_ENDPOINT_ID")
    COMFYUI_URL            = os.getenv("COMFYUI_URL", "")

    # Budget guard
    MONTHLY_BUDGET_USD     = 20.00
    COST_PER_GPU_HOUR      = 0.39
    MAX_GPU_HOURS_PER_MONTH = 36

    # Video specs
    TARGET_VIDEO_DURATION_MIN = 9.5
    CLIPS_PER_VIDEO        = 36
    CLIP_DURATION_SEC      = 5.0
    FPS                    = 30

    # Quality gates
    MIN_SHARPNESS_SCORE    = 85
    MAX_MOTION_SCORE       = 0.8
    MIN_CLIP_DURATION      = 4.5
    MAX_RETRY_ATTEMPTS     = 3

    # Pacing
    MAX_VISUAL_GAP_SEC     = 22
    CROSSFADE_DURATION     = 0.3
    BGM_DUCK_DB            = -22

    # Models
    LLM_MODEL              = "gpt-4o-mini"
