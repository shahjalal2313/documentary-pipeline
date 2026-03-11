# 🚀 Wan 2.2 Optimization & Quality Task List

## 📋 Status Overview
- [x] **Task 1: Prompt Engineering Upgrade** (Done)
- [x] **Task 2: Negative Prompt Injection** (Done)
- [x] **Task 3: Environment Setup (Pod Optimization)** (Done)
- [x] **Task 4: Workflow Optimization (Speed/SageAttention)** (Done)
- [x] **Task 5: Triple Sampler Refactoring (Quality Ceiling)** (Done)
- [ ] **Task 6: Final Validation & Benchmark** (In Progress)

---

## 🛠️ Detailed Task Breakdown

### ✅ Task 1: Prompt Engineering Upgrade
- [x] Update `config/prompts/script_system.txt` with 4-part structure instructions.
- [x] Update `modules/02_script.py` to enforce cinematic constraints.
- [x] Regenerate a test script to verify prompt quality.

### ✅ Task 2: Negative Prompt Injection
- [x] Modify `modules/04_video.py` to dynamically inject the English "Temporal Stability" negative prompt into Node 72.
- [x] Remove legacy Chinese negative prompts from the workflow injection.

### ✅ Task 3: Environment Setup (Pod Optimization)
- [x] Update `pod_setup.sh` to include `pip install sageattention`.
- [x] Verify installation on the active pod.

### ✅ Task 4: Workflow Optimization (Speed/SageAttention)
- [x] Update `workflows/wan2_template.json` to enable SageAttention 2.2 and TeaCache.
- [x] Inject SageAttention and TeaCache nodes into the workflow via `modules/04_video.py`.

### ✅ Task 5: Triple Sampler Refactoring (Quality Ceiling)
- [x] Redesign `wan2_template.json` to use the 3-stage chain.
- [x] Update `04_video.py` to handle the new node IDs for seeds and prompts.

### ⏳ Task 6: Final Validation & Benchmark
- [ ] Run a 3-scene batch test.
- [ ] Compare time-per-clip (Target: <4 mins on 4090).
- [ ] Compare visual consistency and "flicker" reduction.
