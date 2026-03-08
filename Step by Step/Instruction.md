# Strict
Never Implement your creativity or Inovation Just follow step by step instructions as Documented

# prompt
check and impliment accordingly follow as it is don't add your own creativity or innovation.Always activate venv before running any python script.

# 🚀 RunPod Environment Persistence (CRITICAL)
Since we are using Python 3.12 on RunPod "Spot Instances," the system environment is wiped upon termination. We have moved the fixed environment to the **Network Volume** to prevent re-installation.

### 1. How to Restore Environment on a NEW Pod:
After starting a new pod and attaching your Network Volume, run this command FIRST:
```bash
source /workspace/venv_persistent/bin/activate
```
This restores:
*   **Numpy 1.26.4** (Bridge version for 3.12 compatibility)
*   **Chatterbox-TTS** (With `pkgutil` monkeypatch)
*   **OpenCV < 4.10** (Compatible with Numpy 1.x)

### 2. Manual Monkeypatch for Module 3 (If needed):
If `chatterbox` fails with `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`, ensure this is at the top of your script:
```python
import pkgutil
if not hasattr(pkgutil, 'ImpImporter'):
    class ImpImporter: pass
    pkgutil.ImpImporter = ImpImporter
```

### 3. SSH Auto-Discovery & Setup:
*   **Passwordless Login:** Add your local public key to **RunPod Settings -> SSH Public Keys**:
    `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO3XhK80wII4fnnA5o5Yk6WRA4KXmbgwysvsjzGCCpGP digital outlet@Shanto`
*   **Auto-Find IP & Port:** Every time you start your pod, run the helper script in your local PowerShell to get the correct SSH/SCP commands:
    ```powershell
    python get_pod_details.py
    ```

### 4. File Paths:
*   **Local Project:** `F:\YA Business\documentary-pipeline`
*   **RunPod Volume:** `/workspace/`
*   **Persistent Venv:** `/workspace/venv_persistent/`
