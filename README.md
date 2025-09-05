<h1>INIVerse Max SDXL - Custom Preset Workflows</h1>

[![RunPod](https://api.runpod.io/badge/runpod-workers/worker-a1111)](https://www.runpod.io/console/hub/runpod-workers/worker-a1111)

> Modified to perfection by [Ruminansi_Art](https://github.com/ruminansiart-arch)

Runs [Automatic1111 Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) with custom preset workflows optimized for n8n automation and frontend testing.

Comes pre-packaged with:
- **INIVerse_Max** model
- **4x-UltraSharp** upscaler
- **ADetailer** for face fixing

---

## 🚀 Preset Workflows

The `input` object accepts a `workflow` parameter with three preset options:

### 1. Low Quality (Fast & Cheap)
- **Workflow:** `{"workflow": "low"}`
- Generates 512x768 image using T2I only.
- Perfect for testing and quick iterations.

### 2. Medium Quality (Balanced)
- **Workflow:** `{"workflow": "medium"}`
- Generates 512x768 image, then upscales 2x with I2I High-Res Fix + ADetailer.
- Great balance of quality and speed.

### 3. Max Quality (4K Ultimate)
- **Workflow:** `{"workflow": "max"}`
- Generates 512x768 image, upscales 4x with Ultrasharp, then refines with I2I + ADetailer.
- For final 4K resolution output.

---

## 🛠️ Refine Any Image Tool

Separately refine ANY image (from presets or external sources) with 2x upscale + enhanced details:

```json
{
  "input": {
    "refine_mode": true,
    "image": "base64_image_string_here"
  }
}

json```

## 🛠️ Refine Any Image Tool

Separately refine ANY image (from presets or external sources) with 2x upscale + enhanced details:

📋 Example Request

```json

{
  "input": {
    "workflow": "medium",
    "prompt": "a photograph of an astronaut riding a horse",
    "negative_prompt": "text, watermark, blurry, low quality",
    "steps": 30,
    "cfg_scale": 7.5,
    "width": 512,
    "height": 768,
    "seed": -1
  }
}
