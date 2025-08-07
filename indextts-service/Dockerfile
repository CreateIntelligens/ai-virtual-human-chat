# IndexTTS API Dockerfile
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝ffmpeg和PyTorch (CUDA版本)
RUN pip install --no-cache-dir ffmpeg && \
    pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 複製requirements檔案並安裝其他依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製setup相關檔案
COPY setup.py pyproject.toml README.md ./

# 複製indextts模組
COPY indextts/ ./indextts/

# 安裝IndexTTS包
RUN pip install -e .

# 複製其他專案檔案
COPY . .

# 設定CUDA環境變數
ENV CUDA_HOME=/usr/local/cuda
ENV CUDA_PATH=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 重新編譯CUDA kernel以獲得更好的性能
RUN pip install -e . --no-deps --no-build-isolation || echo "CUDA kernel compilation failed, will use fallback"

# 創建必要的目錄
RUN mkdir -p checkpoints outputs

# 注意：模型文件將在運行時檢查並下載，避免 Docker build 時的網路問題

# 暴露端口
EXPOSE 6008

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:6008/docs || exit 1

# 啟動命令
CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "6008"]
