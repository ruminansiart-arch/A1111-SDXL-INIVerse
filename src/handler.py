import time
import runpod
import requests
import base64
from PIL import Image
from io import BytesIO
from requests.adapters import HTTPAdapter, Retry

LOCAL_URL = "http://127.0.0.1:3000/sdapi/v1"
automatic_session = requests.Session()
retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[502, 503, 504])
automatic_session.mount('http://', HTTPAdapter(max_retries=retries))

def wait_for_service(url):
    retries = 0
    while True:
        try:
            requests.get(url, timeout=120)
            return
        except requests.exceptions.RequestException:
            retries += 1
            if retries % 15 == 0:
                print("Service not ready yet. Retrying...")
        except Exception as err:
            print("Error: ", err)
        time.sleep(0.2)

def call_api(endpoint, payload):
    response = automatic_session.post(url=f'{LOCAL_URL}/{endpoint}', json=payload, timeout=600)
    return response.json()

def get_image_size(base64_str):
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        return image.size
    except Exception as e:
        print(f"Error getting image dimensions: {e}")
        return (512, 512)

def handler(event):
    job_input = event["input"]
    
    # OPTION 1: REFINE ANY IMAGE (STANDALONE)
    if job_input.get("refine_mode", False):
        init_image = job_input["image"]
        original_width, original_height = get_image_size(init_image)
        target_width = original_width * 2
        target_height = original_height * 2
        
        refine_payload = {
            "init_images": [init_image],
            "prompt": job_input.get("prompt", "high quality, detailed, sharp"),
            "negative_prompt": job_input.get("negative_prompt", "blurry, noisy, bad quality"),
            "width": target_width,
            "height": target_height,
            "cfg_scale": job_input.get("cfg_scale", 5),
            "steps": job_input.get("steps", 40),
            "denoising_strength": 0.3,
            "alwayson_scripts": {
                "adetailer": {
                    "args": [{"ad_model": "face_yolov8n.pt", "ad_confidence": 0.3}]
                }
            }
        }
        return call_api('img2img', refine_payload)

    # OPTION 2: 3 PRESET WORKFLOWS
    workflow_type = job_input.get("workflow", "low")
    result = None

    t2i_payload = {
        "prompt": job_input["prompt"],
        "negative_prompt": job_input.get("negative_prompt", ""),
        "width": 512,
        "height": 768,
        "cfg_scale": job_input.get("cfg_scale", 7.5),
        "steps": job_input.get("steps", 30),
        "seed": job_input.get("seed", -1)
    }

    if workflow_type == "low":
        result = call_api('txt2img', t2i_payload)

    elif workflow_type == "medium":
        t2i_result = call_api('txt2img', t2i_payload)
        init_image = t2i_result['images'][0]

        i2i_payload = {
            "init_images": [init_image],
            "prompt": t2i_payload["prompt"],
            "negative_prompt": t2i_payload["negative_prompt"],
            "width": 1024,
            "height": 1536,
            "cfg_scale": t2i_payload["cfg_scale"],
            "steps": t2i_payload["steps"],
            "denoising_strength": 0.3,
            "alwayson_scripts": {
                "adetailer": {
                    "args": [{"ad_model": "face_yolov8n.pt", "ad_confidence": 0.3}]
                }
            }
        }
        result = call_api('img2img', i2i_payload)

    elif workflow_type == "max":
        t2i_result = call_api('txt2img', t2i_payload)
        init_image = t2i_result['images'][0]

        extras_payload = {
            "image": init_image,
            "upscaling_resize": 4,
            "upscaler_1": "4x-UltraSharp"
        }
        extras_result = call_api('extra-single-image', extras_payload)
        upscaled_image = extras_result['image']

        i2i_payload = {
            "init_images": [upscaled_image],
            "prompt": t2i_payload["prompt"],
            "negative_prompt": t2i_payload["negative_prompt"],
            "width": 2048,
            "height": 3072,
            "cfg_scale": 5,
            "steps": 20,
            "denoising_strength": 0.2,
            "alwayson_scripts": {
                "adetailer": {
                    "args": [{"ad_model": "face_yolov8n.pt", "ad_confidence": 0.3}]
                }
            }
        }
        result = call_api('img2img', i2i_payload)

    return result

if __name__ == "__main__":
    wait_for_service(url=f'{LOCAL_URL}/sd-models')
    print("WebUI API Service is ready. Starting RunPod Serverless...")
    runpod.serverless.start({"handler": handler})
