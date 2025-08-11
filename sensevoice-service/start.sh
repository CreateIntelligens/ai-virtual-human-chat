#!/bin/bash

# SenseVoice API 啟動腳本

echo "🚀 啟動 SenseVoice API 服務..."

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查 nvidia-docker 支援
if ! docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi > /dev/null 2>&1; then
    echo "⚠️  警告: GPU 支援可能不可用，將使用 CPU 模式"
    export SENSEVOICE_DEVICE=cpu
fi

# 構建並啟動服務
echo "📦 構建 Docker 映像..."
docker-compose build

echo "🔄 啟動服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
if curl -s http://localhost:50002/ > /dev/null; then
    echo "✅ 服務啟動成功！"
    echo "🌐 API 文檔: http://localhost:50002/docs"
    echo "📊 記憶體監控: http://localhost:50002/memory"
    echo "📋 查看日誌: docker-compose logs -f sensevoice-api"
else
    echo "❌ 服務啟動失敗，請檢查日誌:"
    docker-compose logs sensevoice-api
fi
