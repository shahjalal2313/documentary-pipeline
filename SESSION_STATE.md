# Session State: Phase 3.2 — HunyuanVideo-Foley Integration
**Date:** March 9, 2026

## ✅ Completed in this Session
1.  **Archived Old 3.2:** Moved `06_assembly.py` and test outputs to `F:\YA Business\archive\Phase3\Old_3.2_Assembly`.
2.  **Code Implemented:** `modules/03b_foley.py` is ready with normalization, duration alignment, and profile filtering.
3.  **LLM Prompt Updated:** `modules/02_script.py` now generates `sound_profile` tags (`ambient`, `foley`, `silent`, `music_only`).
4.  **Pod Environment Setup:**
    *   Cloned `HunyuanVideo-Foley` to `/workspace/`.
    *   Installed `unzip` on the OS.
    *   Installed dependencies in `/workspace/venv_persistent`.

## 🚧 Current Blocker: Disk Quota
The model download (`9.6GB`) failed because the `/workspace` volume was full. The user is currently restarting the pod with an expanded volume (100GB+).

## 🚀 Next Steps (Immediate)
1.  **Run Discovery:** Run `.\venv\Scripts\python.exe get_pod_details.py` to get the new IP and Port.
2.  **Resume Download:** Use `wget -c` via SSH to resume the 10GB model download:
    ```bash
    ssh -p [PORT] root@[IP] "source /workspace/venv_persistent/bin/activate && cd /workspace/HunyuanVideo-Foley/pretrained_models && wget -c https://huggingface.co/tencent/HunyuanVideo-Foley/resolve/main/hunyuanvideo_foley.pth"
    ```
3.  **Verify Weights:** Ensure all `.pth` files are in `pretrained_models`.
4.  **Final Validation:** Run a test clip through `modules/03b_foley.py` on the pod and verify 48kHz output.
