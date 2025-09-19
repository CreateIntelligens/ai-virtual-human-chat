# Use the latest vLLM image with CUDA support
FROM vllm/vllm-openai:latest

# Set environment variables for RTX 5070 Ti compatibility
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
ENV CUDA_LAUNCH_BLOCKING=1
ENV TORCH_CUDA_ARCH_LIST="8.9"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libsndfile1 \
    libsm6 \
    libxext6 \
    && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python


# Upgrade PyTorch to latest version with better GPU support
RUN pip install --no-cache-dir --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# COPY assets /app/assets
COPY indextts /app/indextts
COPY tools /app/tools
COPY patch_vllm.py /app/patch_vllm.py
COPY api_server.py /app/api_server.py
COPY convert_hf_format.py /app/convert_hf_format.py
COPY convert_hf_format.sh /app/convert_hf_format.sh
COPY entrypoint.sh /app/entrypoint.sh
COPY custom_dict.json /app/custom_dict.json

RUN sed -i 's/\r$//' /app/entrypoint.sh /app/convert_hf_format.sh && \
    chmod +x /app/entrypoint.sh /app/convert_hf_format.sh

ENTRYPOINT ["/app/entrypoint.sh"]
