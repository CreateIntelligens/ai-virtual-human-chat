# 使用Python 3.9 slim基礎映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements.txt並安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 設置環境變數
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8888

# 啟動命令
CMD ["python", "web_demo/server.py"]
