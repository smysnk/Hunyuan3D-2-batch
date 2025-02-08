#!/usr/bin/env python3
import argparse
import glob
import os
import re
import requests
import sys
import random
import toml
import colorama
from colorama import Fore, Style

# Initialize colorama (for Windows compatibility, etc.)
colorama.init(autoreset=True)

# --- Standard Colors ---
PREFIX_COLOR = Fore.GREEN      # For prefixes (e.g. "Iteration 1:" or "ℹ️")
TEXT_COLOR   = Fore.CYAN       # For regular text
KEY_COLOR    = Fore.MAGENTA    # For keys in dictionaries
VALUE_COLOR  = Fore.YELLOW     # For dynamic values

# --- Helper Print Functions ---
def print_info(msg):
    """Info messages with ℹ️ prefix in green."""
    print(Fore.GREEN + "ℹ️  " + Style.RESET_ALL + msg)

def print_success(msg):
    """Success messages start with a green checkmark emoji."""
    print(Fore.GREEN + "✅ " + Style.RESET_ALL + msg)

def print_warning(msg):
    """Warning messages start with a warning emoji."""
    print(Fore.GREEN + "⚠️ " + Style.RESET_ALL + msg)

def print_error(msg):
    """Error messages start with a red 'x' emoji."""
    print(Fore.RED + "❌ " + Style.RESET_ALL + msg)

def print_pretty_dict(d, indent=3):
    """Print each key/value pair on its own line, with keys in magenta and values in yellow."""
    spaces = " " * indent
    for key, value in d.items():
        print(f"{spaces}{KEY_COLOR}{key}{Style.RESET_ALL}: {VALUE_COLOR}{value}{Style.RESET_ALL}")

# --- Configuration Loading ---
def load_config():
    parser = argparse.ArgumentParser(
        description="Generate .glb files by sending data to a server. "
                    "If a config.toml file exists in the current directory, it is loaded exclusively."
    )
    parser.add_argument("--input", type=str, default="input",
                        help="Path to folder containing images (default: input)")
    parser.add_argument("--config", type=str, default="config.toml",
                        help="Path to configuration TOML file (default: config.toml)")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Number of iterations (default: 3)")
    parser.add_argument("--output", type=str, default="output",
                        help="Destination output directory (default: output)")
    parser.add_argument("--seed", type=int,
                        help="Seed value (if not specified, a random value is chosen)")
    parser.add_argument("--octree-resolution", type=int, choices=[256, 384, 512], default=256,
                        help="Octree resolution (256, 384, or 512; default: 256)")
    parser.add_argument("--num-inference_steps", type=int, default=25,
                        help="Number of inference steps (default: 25)")
    parser.add_argument("--face-count", type=int, default=40000,
                        help="Face count (default: 40000)")
    parser.add_argument("--guidance-scale", type=int, default=7,
                        help="Guidance scale (default: 7)")
    parser.add_argument("--endpoint-url", type=str, default="127.0.0.1:8080",
                        help="Endpoint URL (default: 127.0.0.1:8080)")
    parser.add_argument("--upscale", action="store_true",
                        help="Turn on GLB upscaling mode (default: false)")

    default_config = vars(parser.parse_args([]))
    config_file = default_config["config"]

    if os.path.exists(config_file):
        if len(sys.argv) > 1:
            print_error("A config.toml file exists. No command-line arguments are allowed in config mode.")
            sys.exit(1)
        try:
            file_config = toml.load(config_file)
            # The config file name is printed in yellow.
            print_success(TEXT_COLOR + "Loaded configuration from: " + VALUE_COLOR + f"{config_file}" + TEXT_COLOR + ".")
        except Exception as e:
            print_error("Error loading configuration file " + VALUE_COLOR + f"{config_file}" + TEXT_COLOR + f": {e}")
            sys.exit(1)
        # Fill in any missing keys from parser defaults.
        for key, value in default_config.items():
            if key not in file_config:
                file_config[key] = value
        return file_config
    else:
        args = parser.parse_args()
        return vars(args)

# --- Core Processing Function ---
def process_image(image_path, iterations, output, seed, octree, num_inference_steps, face_count, guidance_scale, endpoint_url, upscale):
    """
    Processes a single image by sending it to the server and saving the resulting GLB file(s).
    The naming convention for the output file is:
        {base_name}_{octree}_{num_inference_steps}_{guidance_scale}_{face_count}_{seed_current}.glb
    """
    if not os.path.isfile(image_path):
        print_error("Image file " + VALUE_COLOR + f"{image_path}" + TEXT_COLOR + " does not exist.")
        return

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    os.makedirs(output, exist_ok=True)
    print_info(TEXT_COLOR + "Processing image: " + VALUE_COLOR + f"{image_path}")
    print_info(TEXT_COLOR + "Output directory: " + VALUE_COLOR + f"{output}")

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        print_error("Error reading image data: " + VALUE_COLOR + f"{e}")
        return

    count = 0
    pattern = os.path.join(output, f"{base_name}_{octree}_{num_inference_steps}_{guidance_scale}_{face_count}_*.glb")

    matches = len(glob.glob(pattern))
    if matches >= iterations:
        print_info(PREFIX_COLOR + "process_image():" + Style.RESET_ALL + " " +
                TEXT_COLOR + f"({matches}) file(s) matching pattern " + VALUE_COLOR + f"'{pattern}'" +
                TEXT_COLOR + f" already exists; > {iterations} desired iterations, skipping." + Style.RESET_ALL)
        return 
    
    out_filename = os.path.join(
        output,
        f"{base_name}_{octree}_{num_inference_steps}_{guidance_scale}_{face_count}_{seed}.glb"
    )

    if upscale:
        # In upscale mode, continue only if no files matching the pattern exist.
        def condition():
            return len(glob.glob(pattern)) == 0
    else:
        # In non-upscale mode, continue until we have reached the desired number of iterations.
        def condition():
            return len(glob.glob(pattern)) < iterations
    
    while condition():
        if seed is None:
            seed_current = random.randint(0, 10000000)
        else:
            seed_current = seed

        params = {
            "octree_resolution": octree,
            "num_inference_steps": num_inference_steps,
            "face_count": face_count,
            "guidance_scale": guidance_scale,
            "seed": seed_current
        }

        # Build the output filename using the new naming convention.
        out_filename = os.path.join(
            output,
            f"{base_name}_{octree}_{num_inference_steps}_{guidance_scale}_{face_count}_{seed_current}.glb"
        )
        if os.path.exists(out_filename):
            print_warning(PREFIX_COLOR + f"Iteration {count}:" + Style.RESET_ALL + " " +
                  TEXT_COLOR + "File " + VALUE_COLOR + f"'{out_filename}'" +
                  TEXT_COLOR + " already exists; skipping." + Style.RESET_ALL)
            continue

        print_info(PREFIX_COLOR + f"Iteration {count}:" + Style.RESET_ALL + " " +
              TEXT_COLOR + "Sending POST request with params:" + Style.RESET_ALL)
        print_pretty_dict(params)

        try:
            response = requests.post(
                f"http://{endpoint_url}/generate",
                params=params, data=image_data, headers={"Content-Type": "application/octet-stream"}
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print_error(PREFIX_COLOR + f"Iteration {count}:" + Style.RESET_ALL + " " +
                        TEXT_COLOR + "Request failed: " + VALUE_COLOR + f"{e}" + Style.RESET_ALL)
            continue

        try:
            with open(out_filename, "wb") as out_file:
                out_file.write(response.content)
            print_success(PREFIX_COLOR + f"Iteration {count}:" + Style.RESET_ALL + " " +
                          TEXT_COLOR + "Saved file to " + VALUE_COLOR + f"'{out_filename}'" + Style.RESET_ALL)
        except Exception as e:
            print_error(PREFIX_COLOR + f"Iteration {count}:" + Style.RESET_ALL + " " +
                        TEXT_COLOR + "Failed to save file: " + VALUE_COLOR + f"{e}" + Style.RESET_ALL)
            
        count += 1


# --- Processing Functions ---
def process_folder(config):
    """
    Processes all valid images found in the input folder by calling process_image on each.
    """
    folder = config["input"]
    output = config["output"]
    iterations = config["iterations"]
    seed = config.get("seed")
    octree = config["octree_resolution"]
    num_inference_steps = config["num_inference_steps"]
    face_count = config["face_count"]
    guidance_scale = config["guidance_scale"]
    endpoint_url = config["endpoint_url"]

    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    try:
        image_files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if not f.startswith('.') and os.path.splitext(f)[1].lower() in valid_extensions and
               os.path.isfile(os.path.join(folder, f))
        ]
    except Exception as e:
        print_error("Error reading folder " + VALUE_COLOR + f"{folder}" + TEXT_COLOR + f": {e}")
        return

    if not image_files:
        print_error("No valid image files found in folder " + VALUE_COLOR + f"{folder}" + Style.RESET_ALL)
        return

    image_files.sort()
    for image in image_files:
        process_image(image, iterations, output, seed, octree, num_inference_steps, face_count, guidance_scale, endpoint_url)

def process_glb_upscaling(config):
    """
    GLB Upscaling Mode: Scans the output folder for GLB files whose embedded parameters do not match
    the current settings and re-generates them using the corresponding source image.
    This function locates the source image from the input folder (by matching the base name)
    and calls process_image (with iterations=1) to re-generate the GLB file.
    """
    input_folder = config["input"]
    output = config["output"]
    octree = config["octree_resolution"]
    num_inference_steps = config["num_inference_steps"]
    face_count = config["face_count"]
    guidance_scale = config["guidance_scale"]
    endpoint_url = config["endpoint_url"]
    upscale = config["upscale"]

    print_info(TEXT_COLOR + "Running GLB upscaling mode in output directory: " + VALUE_COLOR + f"{output}")
    # The regex pattern matches filenames in the format:
    # {base_name}_{octree}_{num_inference_steps}_{guidance_scale}_{seed}.glb
    pattern = re.compile(r"^(.*)_([0-9]+)_([0-9]+)_([0-9]+)_([0-9]+)_([0-9]+)\.glb$")
    valid_extensions = {'.jpg', '.jpeg', '.png'}

    for root, _, files in os.walk(output):
        for file in files:
            if not file.endswith(".glb"):
                continue
            match = pattern.match(file)
            if not match:
                continue

            # Extract parameters from the filename.
            base_name, file_octree, file_num_inference_steps, file_guidance, file_face_count, file_seed = match.groups()
            if int(file_octree) >= int(octree) and int(file_num_inference_steps) >= int(num_inference_steps) and int(file_guidance) >= int(guidance_scale):
                print(PREFIX_COLOR + "Skipping:" + Style.RESET_ALL + " " +
                      TEXT_COLOR + f"'{file}' (matches current settings)." + Style.RESET_ALL)
                continue

            # Find the corresponding source image in the input folder.
            source_image_path = None
            for fname in os.listdir(input_folder):
                if fname.startswith('.'):
                    continue
                name, ext = os.path.splitext(fname)
                if name == base_name and ext.lower() in valid_extensions:
                    source_image_path = os.path.join(input_folder, fname)
                    break

            if not source_image_path:
                print_error("No matching source image for " + VALUE_COLOR + f"'{base_name}'" +
                            TEXT_COLOR + f" in '{input_folder}'; skipping '{file}'.")
                continue

            print_info(TEXT_COLOR + "Upscaling " + VALUE_COLOR + f"'{file}'" +
                       TEXT_COLOR + " using source image " + VALUE_COLOR + f"'{source_image_path}'")
            
            # Call process_image for upscaling (1 iteration).
            process_image(
                source_image_path,
                iterations=1,
                output=output,
                seed=int(file_seed),
                octree=octree,
                num_inference_steps=num_inference_steps,
                face_count=face_count,
                guidance_scale=guidance_scale,
                endpoint_url=endpoint_url,
                upscale=upscale
            )

def main():
    config = load_config()
    
    if config["seed"] and config["iterations"] != 1:
        print_warning("Seed must not be set when running with more than 1 iteration, setting iterations to 1.")
        config["iterations"] = 1

    if not os.path.isdir(config.get("input")):
        print_error(VALUE_COLOR + f"'{config.get('input')}'" + TEXT_COLOR + " is not a valid folder.")
        sys.exit(1)

    os.makedirs(config["output"], exist_ok=True)

    print(PREFIX_COLOR + "Current Settings:" + Style.RESET_ALL)
    print_pretty_dict(config, indent=2)
    print()  # Blank line for spacing.

    if config.get("upscale"):
        process_glb_upscaling(config)
    else:
        process_folder(config)

if __name__ == "__main__":
    main()
