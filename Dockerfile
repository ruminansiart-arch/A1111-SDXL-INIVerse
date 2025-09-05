# Download models
FROM alpine/git:2.43.0 as download

RUN apk add --no-cache wget curl

# Download INIVerse_Max with better error handling
RUN \
    echo "API key starts with: 92bcbcdf1f..." && \
    echo "Testing API key..." && \
    curl -s -H "Authorization: Bearer YOURCIVITAIKEY" "https://civitai.com/api/v1/models" > /tmp/test_response && \
    echo "API test response: $(head -c 200 /tmp/test_response)" && \
    echo "Downloading model with curl (handles redirects better)..." && \
    curl -L -H "Authorization: Bearer YOURCIVITAIKEY" -o /INIVerse_Max.safetensors "https://civitai.com/api/download/models/1150354?type=Model&format=SafeTensor&size=full&fp=fp16" && \
    echo "Download completed. File size: $(wc -c < /INIVerse_Max.safetensors) bytes" && \
    if [ $(wc -c < /INIVerse_Max.safetensors) -lt 1000000 ]; then \
        echo "ERROR: File too small - likely download failed!"; \
        head -c 200 /INIVerse_Max.safetensors; \
        exit 1; \
    fi
    
# Download 4x-Ultrasharp
RUN wget -q -O /4x-UltraSharp.pth "https://huggingface.co/lokCX/4x-Ultrasharp/resolve/main/4x-UltraSharp.pth?download=true" && \
    echo "4x-UltraSharp downloaded: $(wc -c < /4x-UltraSharp.pth) bytes"

# Build image
FROM python:3.10.14-slim

ARG A1111_RELEASE=v1.9.3
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_PREFER_BINARY=1 \
    ROOT=/stable-diffusion-webui \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt install -y \
    fonts-dejavu-core rsync git jq moreutils aria2 wget libgoogle-perftools-dev libtcmalloc-minimal4 procps libgl1 libglib2.0-0 && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/* && apt-get clean -y

RUN --mount=type=cache,target=/root/.cache/pip \
    git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git && \
    cd stable-diffusion-webui && \
    git reset --hard ${A1111_RELEASE} && \
    pip install xformers && \
    pip install -r requirements_versions.txt && \
    python -c "from launch import prepare_environment; prepare_environment()" --skip-torch-cuda-test

# Create folders and copy models
RUN mkdir -p ${ROOT}/models/Stable-diffusion
RUN mkdir -p ${ROOT}/models/ESRGAN
COPY --from=download /INIVerse_Max.safetensors ${ROOT}/models/Stable-diffusion/
COPY --from=download /4x-UltraSharp.pth ${ROOT}/models/ESRGAN/

# Verify models are present
RUN echo "Model verification:" && \
    ls -la ${ROOT}/models/Stable-diffusion/ && \
    ls -la ${ROOT}/models/ESRGAN/ && \
    echo "INIVerse_Max size: $(wc -c < ${ROOT}/models/Stable-diffusion/INIVerse_Max.safetensors) bytes" && \
    echo "4x-UltraSharp size: $(wc -c < ${ROOT}/models/ESRGAN/4x-UltraSharp.pth) bytes"

# Install app dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY test_input.json .
ADD src .
RUN chmod +x /start.sh

CMD /start.sh