# Verification Issue Report - Phase 3.3

## Status: BLOCKED
**Timestamp:** 2026-03-10 05:54 AM
**Phase:** Phase 3.3 - Rough Cut Engine Verification

## Problem Description
Attempted to run the 2-scene verification test (Wan 2.2 Video + Remote Foley) with Pod ID `a82hvvg6ly20n0`. 
1.  **ComfyUI Proxy:** Returning `404 Not Found` at `https://a82hvvg6ly20n0-8188.proxy.runpod.net/system_stats`.
2.  **SSH Service:** `Connection refused` on port `10235` at IP `203.57.40.62`.

## Action Required
- Ensure **SSH access** is enabled on the RunPod instance.
- Ensure the **ComfyUI server** is running and listening on port 8188.
- Once connectivity is verified, re-run `verify_2_scenes.py`.
## Scene 1 Failure
- Error: [Errno 2] No such file or directory: 'workflows\\wan2_template.json'
- Timestamp: 2026-03-10 15:16:59

## Scene 2 Failure
- Error: [Errno 2] No such file or directory: 'workflows\\wan2_template.json'
- Timestamp: 2026-03-10 15:16:59

## Scene 1 Failure
- Error: Remote Foley failed: Warning: Permanently added '[203.57.40.62]:10093' (ED25519) to the list of known hosts.
python: can't open file '/workspace/HunyuanVideo-Foley/inference.py': [Errno 2] No such file or directory

- Timestamp: 2026-03-10 15:20:30

## Scene 2 Failure
- Error: Remote Foley failed: python: can't open file '/workspace/HunyuanVideo-Foley/inference.py': [Errno 2] No such file or directory

- Timestamp: 2026-03-10 15:22:31

## Scene 1 Failure
- Error: Remote Foley failed: Traceback (most recent call last):
  File "/workspace/HunyuanVideo-Foley/infer.py", line 304, in <module>
    main()
  File "/workspace/HunyuanVideo-Foley/infer.py", line 283, in main
    model_dict, cfg = load_model(args.model_path, args.config_path, device, enable_offload=args.enable_offload, model_size=args.model_size)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/utils/model_utils.py", line 297, in load_model
    foley_model = HunyuanVideoFoley(cfg, dtype=torch.bfloat16, device=device).to(device=device, dtype=torch.bfloat16)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/venv_persistent/lib/python3.12/site-packages/diffusers/configuration_utils.py", line 658, in inner_init
    init(self, *args, **init_kwargs)
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/hifi_foley.py", line 492, in __init__
    SingleStreamBlock(
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/hifi_foley.py", line 341, in __init__
    self.linear2 = ConvMLP(hidden_size, hidden_size * mlp_ratio, kernel_size=3, padding=1, **factory_kwargs)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/nn/mlp_layers.py", line 145, in __init__
    self.w2 = ChannelLastConv1d(hidden_dim, dim, bias=False, kernel_size=kernel_size, padding=padding, **factory_kwargs)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/venv_persistent/lib/python3.12/site-packages/torch/nn/modules/conv.py", line 341, in __init__
    super().__init__(
  File "/workspace/venv_persistent/lib/python3.12/site-packages/torch/nn/modules/conv.py", line 170, in __init__
    torch.empty(
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 36.00 MiB. GPU 0 has a total capacity of 23.53 GiB of which 22.31 MiB is free. Process 176 has 14.04 GiB memory in use. Including non-PyTorch memory, this process has 9.46 GiB memory in use. Of the allocated memory 8.89 GiB is allocated by PyTorch, and 136.62 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

- Timestamp: 2026-03-10 15:41:00

## Scene 2 Failure
- Error: Remote Foley failed: Traceback (most recent call last):
  File "/workspace/HunyuanVideo-Foley/infer.py", line 304, in <module>
    main()
  File "/workspace/HunyuanVideo-Foley/infer.py", line 283, in main
    model_dict, cfg = load_model(args.model_path, args.config_path, device, enable_offload=args.enable_offload, model_size=args.model_size)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/utils/model_utils.py", line 297, in load_model
    foley_model = HunyuanVideoFoley(cfg, dtype=torch.bfloat16, device=device).to(device=device, dtype=torch.bfloat16)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/venv_persistent/lib/python3.12/site-packages/diffusers/configuration_utils.py", line 658, in inner_init
    init(self, *args, **init_kwargs)
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/hifi_foley.py", line 492, in __init__
    SingleStreamBlock(
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/hifi_foley.py", line 341, in __init__
    self.linear2 = ConvMLP(hidden_size, hidden_size * mlp_ratio, kernel_size=3, padding=1, **factory_kwargs)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/HunyuanVideo-Foley/hunyuanvideo_foley/models/nn/mlp_layers.py", line 145, in __init__
    self.w2 = ChannelLastConv1d(hidden_dim, dim, bias=False, kernel_size=kernel_size, padding=padding, **factory_kwargs)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/venv_persistent/lib/python3.12/site-packages/torch/nn/modules/conv.py", line 341, in __init__
    super().__init__(
  File "/workspace/venv_persistent/lib/python3.12/site-packages/torch/nn/modules/conv.py", line 170, in __init__
    torch.empty(
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 36.00 MiB. GPU 0 has a total capacity of 23.53 GiB of which 22.31 MiB is free. Process 176 has 14.04 GiB memory in use. Including non-PyTorch memory, this process has 9.46 GiB memory in use. Of the allocated memory 8.89 GiB is allocated by PyTorch, and 136.62 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

- Timestamp: 2026-03-10 15:44:27

