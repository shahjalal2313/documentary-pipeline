# 🛠️ BUILD_GUIDE.md: Building your Custom RunPod Image

This guide shows you how to build your 4090-optimized Docker image on a temporary RunPod and push it to your GitHub account (free storage).

---

### Step 3: Setup GitHub Personal Access Token (PAT)
To push your image to GitHub, you need a token.
1. Go to: [GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)](https://github.com/settings/tokens).
2. Click **Generate new token (classic)**.
3. Name it: `RunPod Docker Push`.
4. Select scope: **`write:packages`** (required).
5. **Copy the token** and save it somewhere safe (it starts with `ghp_`).

---

### Step 4: Perform the Cloud Build (On a RunPod)
Don't build this on your local machine (too slow). Use a 4090 for 15 minutes.

1. **Launch a Pod:** Any 4090 pod with the "Default" template.
2. **SSH into the Pod** or open the Web Terminal.
3. **Copy the Dockerfile content** from your local `documentary-pipeline/docker/Dockerfile`.
4. **On the Pod:**
   ```bash
   mkdir build-docker && cd build-docker
   nano Dockerfile  # Paste the content and save (Ctrl+O, Enter, Ctrl+X)
   ```
5. **Run these commands:**

```bash
# 1. Log in to GitHub Container Registry
# (Enter your GitHub username and PASTE the PAT token when prompted for password)
docker login ghcr.io -u YOUR_GITHUB_USERNAME

# 2. Build the image (Takes ~10-15 mins)
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/documentary-engine:latest .

# 3. Push to GitHub (Takes ~2 mins)
docker push ghcr.io/YOUR_GITHUB_USERNAME/documentary-engine:latest
```

---

### Step 5: Create RunPod Template
Once the push is finished, go to your RunPod Dashboard:
1. Click **Templates** > **New Template**.
2. **Template Name:** `Documentary-AI-V1`.
3. **Container Image:** `ghcr.io/YOUR_GITHUB_USERNAME/documentary-engine:latest`.
4. **Container Disk:** 100GB (Enough for the image and the 50GB models).
5. **Expose Ports:** `8188` (for ComfyUI).

---

### Step 6: Launch & Automate
Now, every time you want to work:
1. Click **Deploy** > Select your `Documentary-AI-V1` template.
2. **Choose ANY location** that has a 4090.
3. Wait ~12 minutes (models download in background).
4. Open the proxy URL: `https://POD_ID-8188.proxy.runpod.net`
5. **ComfyUI is ready!**
