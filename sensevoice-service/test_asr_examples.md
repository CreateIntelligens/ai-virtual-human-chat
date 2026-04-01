# SenseVoice ASR API 使用範例

## 基本 curl 命令

### 單個音頻文件

```bash
curl -X POST "http://localhost:8000/api/v1/asr" \
  -F "files=@audio.wav" \
  -F "keys=audio.wav" \
  -F "lang=auto" \
  -H "accept: application/json"
```

### 指定語言（中文）

```bash
curl -X POST "http://localhost:8000/api/v1/asr" \
  -F "files=@chinese_audio.wav" \
  -F "keys=chinese_audio" \
  -F "lang=zh" \
  -H "accept: application/json"
```

### 多個音頻文件

```bash
curl -X POST "http://localhost:8000/api/v1/asr" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F "files=@audio3.wav" \
  -F "keys=audio1,audio2,audio3" \
  -F "lang=auto" \
  -H "accept: application/json"
```

## 語言選項

- `auto`: 自動檢測（預設）
- `zh`: 中文（普通話）
- `en`: 英文
- `yue`: 粵語
- `ja`: 日文
- `ko`: 韓文
- `nospeech`: 無語音

## 使用 Shell 腳本

已提供 `test_asr_curl.sh` 腳本，使用方法：

```bash
# 給予執行權限
chmod +x test_asr_curl.sh

# 使用預設語言（auto）
./test_asr_curl.sh audio.wav

# 指定語言
./test_asr_curl.sh audio.wav zh
./test_asr_curl.sh english_audio.wav en
```

## Python 範例

```python
import requests

# API 端點
url = "http://localhost:8000/api/v1/asr"

# 準備文件
files = {
    'files': ('audio.wav', open('audio.wav', 'rb'), 'audio/wav')
}

# 準備表單數據
data = {
    'keys': 'audio.wav',
    'lang': 'auto'
}

# 發送請求
response = requests.post(url, files=files, data=data)

# 打印結果
print(response.json())
```

## 返回格式

API 會返回包含以下字段的 JSON：

```json
{
  "result": [
    {
      "key": "audio.wav",
      "text": "辨識後的完整文字（繁體，包含情感標記）",
      "raw_text": "原始辨識文字（繁體）",
      "clean_text": "清理後的文字（繁體，移除所有標記）"
    }
  ]
}
```

## 記憶體監控端點

### 查看 GPU 記憶體使用

```bash
curl http://localhost:8000/memory
```

### 手動清理 GPU 記憶體

```bash
curl -X POST http://localhost:8000/memory/cleanup
```

## 完整測試流程

```bash
# 1. 檢查服務狀態
curl http://localhost:8000/

# 2. 檢查 GPU 記憶體
curl http://localhost:8000/memory

# 3. 執行 ASR 辨識
curl -X POST "http://localhost:8000/api/v1/asr" \
  -F "files=@test.wav" \
  -F "keys=test" \
  -F "lang=zh"

# 4. 再次檢查記憶體使用
curl http://localhost:8000/memory

# 5. 如需要，手動清理記憶體
curl -X POST http://localhost:8000/memory/cleanup
```
