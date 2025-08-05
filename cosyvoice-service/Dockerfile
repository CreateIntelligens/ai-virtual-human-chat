FROM python:3.9-slim

# 設定非互動模式
ENV DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# 複製所有必要的程式碼
COPY cosyvoice/ ./cosyvoice/
COPY third_party/ ./third_party/
COPY runtime/ ./runtime/
COPY config/ ./config/

# 設定 Python 路徑
ENV PYTHONPATH=/app:/app/third_party/Matcha-TTS

# 創建模型目錄
RUN mkdir -p /app/models

# 暴露端口
EXPOSE 50001

# 設定啟動命令
CMD ["python3", "runtime/python/fastapi/server.py", "--port", "50001", "--model_dir", "/app/models/trained_models20250801/cosyvoice2/"]
