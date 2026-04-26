# Local Apple Silicon ComfyUI setup

Tested in this repo on macOS 26.4.1 / Apple M5 Max with a repo-local `.venv`.

## Python environment

ComfyUI `README.md` currently says Python 3.13 is very well supported (fallback: 3.12), and `pyproject.toml` requires Python `>=3.10`.

This setup uses:

- Python `3.13.4`
- repo-local virtualenv: `.venv`
- PyTorch `2.11.0` with MPS enabled

Bootstrap commands used:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Quick MPS verification command:

```bash
source .venv/bin/activate
python - <<'PY'
import torch
print(torch.__version__)
print(torch.backends.mps.is_available())
PY
```

## Launch commands

Primary launcher:

```bash
./scripts/run_comfyui.sh
```

This activates `.venv`, enables `PYTORCH_ENABLE_MPS_FALLBACK=1`, and runs:

```bash
python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --preview-method auto
```

Safer/lower-pressure launch mode:

```bash
./scripts/run_comfyui_safe.sh
```

That adds:

- `--cpu-vae`
- `--cache-none`

## DreamShaper XL checkpoint

Installed checkpoint:

- filename: `DreamShaperXL1.0Alpha2_fixedVae_half_00001_.safetensors`
- source URL: `https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaperXL1.0Alpha2_fixedVae_half_00001_.safetensors?download=true`
- destination: `models/checkpoints/DreamShaperXL1.0Alpha2_fixedVae_half_00001_.safetensors`
- SHA256: `0f1b80cfe81b9c3bde7fdcbf6898897b2811b27be1df684583c3d85cbc9b1fa4`

The checkpoint is visible to ComfyUI as:

```text
['DreamShaperXL1.0Alpha2_fixedVae_half_00001_.safetensors']
```

## Reusable workflow

Saved API workflow:

- `workflows/dreamshaper_xl_coach_portrait_api.json`

It uses:

- model: `DreamShaperXL1.0Alpha2_fixedVae_half_00001_.safetensors`
- size: `1024x1024`
- steps: `30`
- CFG: `6.5`
- sampler: `dpmpp_2m_sde`
- scheduler: `karras`
- seed: `42424242`

## Automated test generation

Queue the saved workflow against a running local ComfyUI server:

```bash
source .venv/bin/activate
python scripts/generate_test_image.py
```

Optional output prefix override:

```bash
source .venv/bin/activate
python scripts/generate_test_image.py --output-prefix tests/custom_name
```

## Verified outputs

Generated test images:

- `output/tests/server_smoke_check_00001_.png`
- `output/tests/dreamshaper_xl_coach_portrait_00001_.png`

Verified final test image metadata:

- file: `output/tests/dreamshaper_xl_coach_portrait_00001_.png`
- format: `PNG`
- size: `1024x1024`
- mode: `RGB`

## Quick start next time

```bash
./scripts/run_comfyui.sh
```

Then open `http://127.0.0.1:8188/` or queue the saved workflow with:

```bash
source .venv/bin/activate
python scripts/generate_test_image.py
```
