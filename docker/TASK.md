# 📋 TASK.md: Docker-Powered ComfyUI Pipeline Progress

| Status | Step | Description |
| :--- | :--- | :--- |
| ✅ **DONE** | **1. Create Dockerfile** | Defined the "Frozen" environment in `docker/Dockerfile`. |
| ✅ **DONE** | **2. Create Model Downloader** | Embedded in `Dockerfile` to pull 50GB models to NVMe. |
| ⏳ **PENDING** | **3. Setup GitHub Registry** | Get your GitHub Personal Access Token (PAT) ready. |
| ⏳ **PENDING** | **4. Perform Cloud Build** | Run a temporary pod to build & push the image to GitHub. |
| ⏳ **PENDING** | **5. Create RunPod Template** | Add your custom image to the RunPod dashboard. |
| ⏳ **PENDING** | **6. Verification Run** | Launch a 4090 and verify the 12-min auto-setup works. |

---

### Progress Notes:
- **Location:** All docker files moved to `documentary-pipeline/docker/`.
- **Optimization:** `restore_models.sh` logic is now built directly into the image.
- **Next Step:** See `BUILD_GUIDE.md` for Step 3 and 4.
