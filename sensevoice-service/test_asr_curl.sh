#!/bin/bash

# ASR API 測試腳本
# 使用方法: ./test_asr_curl.sh [audio_file_path] [language]

# 設定 API 端點
API_URL="http://localhost:8000/api/v1/asr"

# 取得參數
AUDIO_FILE=${1:-"test_audio.wav"}
LANGUAGE=${2:-"auto"}

# 檢查音頻文件是否存在
if [ ! -f "$AUDIO_FILE" ]; then
    echo "錯誤: 找不到音頻文件 '$AUDIO_FILE'"
    echo "使用方法: $0 <audio_file_path> [language]"
    echo "語言選項: auto, zh, en, yue, ja, ko, nospeech"
    exit 1
fi

# 取得文件名（不含路徑）
FILENAME=$(basename "$AUDIO_FILE")

echo "========================================="
echo "測試 SenseVoice ASR API"
echo "========================================="
echo "API 端點: $API_URL"
echo "音頻文件: $AUDIO_FILE"
echo "語言: $LANGUAGE"
echo "========================================="

# 執行 curl 請求
curl -X POST "$API_URL" \
  -F "files=@$AUDIO_FILE" \
  -F "keys=$FILENAME" \
  -F "lang=$LANGUAGE" \
  -H "accept: application/json"

echo ""
echo "========================================="
echo "請求完成"
echo "========================================="
