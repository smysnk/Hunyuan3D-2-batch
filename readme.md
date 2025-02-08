# Hunyuan3D 2.0 Integration Helper

This repository contains helper scripts to integrate with [Hunyuan3D 2.0](https://github.com/Tencent/Hunyuan3D-2) via its HTTP API. It includes:

- **A custom `api_server.py`** providing improvements over the current server in Hunyuan3D-2:
  - It handles larger upload sizes by avoiding base64-encoded images in JSON.
  - It supports additional parameters: `octree_resolution`, `num_inference_steps`, `face_count`, `guidance_scale`, and more.
- **A `generate_glb.py`** script that orchestrates bulk image-to-3D generation and optional upscaling.

## Overview

**Hunyuan3D 2.0** is an advanced large-scale 3D synthesis system that can generate detailed, textured 3D assets, built upon:

- **Hunyuan3D-DiT**: A shape generation model using a scalable flow-based diffusion transformer.
- **Hunyuan3D-Paint**: A texture synthesis model leveraging geometric and diffusion priors to produce high-quality textures.

This helper repository focuses on:
1. **Streamlined 3D shape generation** by automating requests to a local or remote Hunyuan3D-2 server.
2. **Upscaling** of selected 3D outputs, using the same seed but higher quality settings.

## Installation

1. **Clone This Repo into Hunyuan3D-2**
   - In your existing Hunyuan3D-2 directory:
     ```bash
     cd /path/to/Hunyuan3D-2
     git clone https://your_repo.git Hunyuan3D-2-helpers
     ```
   - You should now have a `Hunyuan3D-2-helpers` folder containing `api_server.py` and `generate_glb.py`.
2. **Dependencies:**
   - These scripts require `requests`, `toml`, and `colorama`.
   - Install them via:
     ```bash
     pip install requests toml colorama
     ```
3. **Run the Provided Server**
   - From within `Hunyuan3D-2-helpers` (or wherever you placed it inside the Hunyuan3D-2 repo), start the custom server:
     ```bash
     python3 api_server.py
     ```
   - This server is configured to allow large file uploads and additional 3D generation parameters.
4. **Generate 3D Assets**
   - In the same directory, run:
     ```bash
     python3 generate_glb.py --input /path/to/images --output /path/to/output --iterations 3
     ```
   - This reads images from `--input`, creates `.glb` files in `--output`, etc.

## Usage and Modes

### Bulk Generation Mode (Default)
- The `generate_glb.py` script will read all valid images in the input folder and generate multiple 3D models for each one based on your settings.
- By default, all parameters (e.g., `octree_resolution`, `num_inference_steps`, etc.) can be specified via command-line or a `config.toml`. A single run will create multiple outputs for each image.

### Upscaling Mode
- After the initial generation, you can inspect the generated `.glb` files in the output folder and remove any that you **do not** want to upscale.
- Re-run the script with the `--upscale` flag (or set `upscale=true` in `config.toml`). The script will:
  - Parse the existing `.glb` files in your `output` directory.
  - Re-generate them at higher resolution or quality settings, but using the **same seed** as before.
  - Create new files reflecting the updated parameters.

## Examples of `config.toml`

Below are a few example configurations. If a `config.toml` is present in the working directory, the script ignores command-line arguments and only uses the config.

### 1. Minimal Config
```toml
input = "input"
output = "output"
iterations = 2
endpoint_url = "127.0.0.1:8080"

# You can leave these as defaults or override:
octree_resolution = 256
num_inference_steps = 25
face_count = 40000
guidance_scale = 7
upscale = false
```

### 2. Higher Quality Settings
```toml
input = "input"
output = "output"
iterations = 3
endpoint_url = "127.0.0.1:8080"

octree_resolution = 384
num_inference_steps = 50
face_count = 60000
guidance_scale = 10
# seed = 12345

upscale = false
```

### 3. Upscaling Mode Config
```toml
input = "input"
output = "output"
iterations = 1
endpoint_url = "127.0.0.1:8080"
octree_resolution = 512
num_inference_steps = 60
face_count = 80000
guidance_scale = 12
upscale = true
```

## Workflow

1. **Prepare Input Images**: Place your images in a folder (e.g., `input`).
2. **Start the Server**: Inside `Hunyuan3D-2-helpers`, run `python3 api_server.py`.
3. **Set Parameters**:
   - Either create or modify `config.toml`, or specify options via command-line.
   - Run `generate_glb.py` in the same directory.
4. **Generate 3D Models**:
   - The script will create 3D `.glb` files in `output`. Each iteration may differ by seed.
5. **Upscale**:
   - Review your output `.glb` files, remove unwanted ones.
   - Enable `--upscale` (or set `upscale=true` in `config.toml`) and run again.
   - The script revisits the remaining `.glb` files, re-generating them at higher quality settings **using the same seed**.

## Example Command Lines

```bash
# Basic usage: create 3D shapes (3 iterations each) for all images in 'input'
python3 generate_glb.py --input input --output output --iterations 3

# Running with a config file (if config.toml is present in the same directory)
python3 generate_glb.py

# Upscaling mode (from command line)
python3 generate_glb.py --upscale --octree-resolution 512 --num-inference_steps 60

# Upscaling mode (via config file)
# (Set "upscale = true" in config.toml and higher parameters)
python3 generate_glb.py
```

