# Hunyuan3D 2.0 Integration Helper

This repository contains helper scripts to integrate with the [Hunyuan3D 2.0 system](https://github.com/Tencent/Hunyuan3D-2) via its HTTP API. It includes a command-line interface for bulk processing of images into 3D assets and optional upscaling.

## Overview

**Hunyuan3D 2.0** is an advanced large-scale 3D synthesis system that can generate detailed, textured 3D assets, built upon:

- **Hunyuan3D-DiT**: A shape generation model using a scalable flow-based diffusion transformer.
- **Hunyuan3D-Paint**: A texture synthesis model leveraging geometric and diffusion priors to produce high-quality textures.

This helper repository focuses on:
1. **Streamlined 3D shape generation** by automating requests to a local or remote Hunyuan3D-2 API server.
2. **Upscaling** of selected 3D outputs, using the same seed but higher quality settings.

## Installation

1. **Clone or Copy:**
   - Clone this helper repository in a convenient location, for example:
     ```bash
     git clone https://your_repo.git Hunyuan3D-2-helpers
     ```
2. **Dependencies:**
   - The scripts in this repo require `requests`, `toml`, and `colorama`.
   - Install them via:
     ```bash
     pip install requests toml colorama
     ```
3. **Server Assumption:**
   - We assume you have a Hunyuan3D 2.0 server (or compatible HTTP API) running at some endpoint. By default, the script expects `127.0.0.1:8080`.

## Usage

1. **Bulk Generation Mode** (Default)
   - In the cloned helper directory, run:
     ```bash
     python3 your_script.py --input /path/to/images --output /path/to/output --iterations 3
     ```
   - The script will read all valid images in the `input` folder, then generate multiple 3D models for each one based on your settings.
   - By default, all parameters (e.g., `octree_resolution`, `num_inference_steps`, etc.) are controlled either via command-line or a `config.toml`. A single run will create multiple outputs for each image.

2. **Upscaling Mode**
   - After the initial generation, you can inspect the generated `.glb` files in the `output` folder and remove any that you **do not** want to upscale.
   - Re-run the script with the `--upscale` flag (or set `upscale=true` in `config.toml`). The script will:
     - Parse the existing `.glb` files in your `output` directory.
     - Re-generate them at higher resolution or quality settings, but using the **same seed** as before.
     - Create new files reflecting the updated parameters.

## Examples of `config.toml`

Below are a few examples of config files that you might use. Note that if a `config.toml` file is present in the working directory, the script will ignore command-line arguments and only use the config.

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

# Higher resolution, more inference steps, etc.
octree_resolution = 384
num_inference_steps = 50
face_count = 60000
guidance_scale = 10

# If 'seed' is omitted, a random seed is chosen per iteration.
# If 'seed' is specified, 1 iteration of that seed will be used.
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

# 'upscale' set to true triggers the script to re-generate existing .glb files
# in 'output' using these higher settings.
upscale = true
```

## Workflow

1. **Prepare Input Images**: Place your images in a folder (e.g., `input`).
2. **Set Parameters**:
   - Either create or modify `config.toml`, or specify options via command-line.
   - Run the script in the directory where it was cloned.
3. **Generate 3D Models**:
   - The script will create 3D `.glb` files in `output`. Each iteration may differ by seed.
4. **Upscale**:
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

