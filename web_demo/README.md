# DH_Live_mini 部署說明

> [!NOTE]
> 本專案專注於在最小硬體資源（無GPU、普通2核4G CPU）環境下實現低延遲的數位人服務部署。

## 服務組件分佈

| 組件   | 部署位置     |
|--------|------------|
| VAD    | Web本地     |
| ASR    | 伺服器本地   |
| LLM    | 雲端服務     |
| TTS    | 伺服器本地   |
| 數位人  | Web本地     |

![deepseek_mermaid_20250428_94e921](https://github.com/user-attachments/assets/505a1602-86c8-4b80-b692-9f6c9dcb19ac)

## 目錄結構

本專案目錄結構如下：
```bash
專案根目錄/
├── models/                  # 本地TTS及ASR模型
│   ├── sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/  # ASR
│   ├── sherpa-onnx-vits-zh-ll/  # TTS                              
├── static/                  # 靜態資源資料夾
│   ├── assets/              # 人物形象資源資料夾
│   ├── assets2/             # 人物2形象資源資料夾
│   ├── common/              # 公共資源資料夾
│   ├── css/                 # CSS樣式資料夾
│   ├── js/                  # JavaScript腳本資料夾
│   ├── DHLiveMini.wasm      # AI推理組件
│   ├── dialog.html          # MiniLive.html包含的純對話iframe頁面
│   ├── dialog_RealTime.html # MiniLive_RealTime.html包含的純對話iframe頁面
│   └── MiniLive.html        # 數位人視頻流主頁面（簡單demo）
│   └── MiniLive_RealTime.html # 數位人視頻流主頁面（即時語音對話頁面，推薦！）
├── voiceapi/                # asr、llm、tts具體設置
└── server.py                # 啟動網頁服務的Python程式
└── server_realtime.py       # 啟動即時語音對話網頁服務的Python程式
```
### 運行專案
（New！）啟動即時語音對話服務：

（注意需要下載本地ASR&TTS模型，並設置openai API進行大模型對話），請看下方配置說明。
```bash
# 切換到DH_live根目錄下
python web_demo/server_realtime.py
```
打開瀏覽器，訪問 http://localhost:8888/static/MiniLive_RealTime.html


如果只是需要簡單演示服務：
```bash
# 切換到DH_live根目錄下
python web_demo/server.py
```
打開瀏覽器，訪問 http://localhost:8888/static/MiniLive.html

## 配置說明

### 1. 替換對話服務網址

對於全流程語音通話demo，在 static/js/dialog_realtime.js 檔案中，找到第1行，將 http://localhost:8888/eb_stream 替換為您自己的對話服務網址。例如：
https://your-dialogue-service.com/eb_stream, 將第二行的websocket url也改為"wss://your-dialogue-service.com/asr?samplerate=16000"

對於簡單演示demo，在 static/js/dialog.js 檔案中，找到第1行，將 http://localhost:8888/eb_stream 替換為您自己的對話服務網址。例如：
https://your-dialogue-service.com/eb_stream

### 2. 模擬對話服務

server.py 提供了一個模擬對話服務的示例。它接收JSON格式的輸入，並流式返回JSON格式的響應。示例代碼如下：

輸入 JSON：
```bash
{
    "prompt": "用戶輸入的對話內容"
}
```
輸出 JSON（流式返回）：
```bash
{
    "text": "返回的部分對話文本",
    "audio": "base64編碼的音頻資料",
    "endpoint": false  // 是否為對話的最後一個片段，true表示結束
}
```
### 3. 全流程的即時語音對話
下載相關模型（可以替換為其他類似模型）：

ASR model: https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2

TTS model: https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-vits-zh-ll.tar.bz2

在voiceapi/llm.py中，按照OpneAI API格式配置大模型介面：

豆包：
```bash
from openai import OpenAI
base_url = "https://ark.cn-beijing.volces.com/api/v3"
api_key = "*****************************"
model_name = "doubao-pro-32k-character-241215"

llm_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)
```

DeepSeek：
```bash
from openai import OpenAI
base_url = "https://api.deepseek.com"
api_key = ""
model_name = "deepseek-chat"

llm_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)
```

### 4. 更換人物形象

要更換人物形象，請將新形象包中的檔案替換 assets 資料夾中的對應檔案。確保新檔案的命名和路徑與原有檔案一致，以避免引用錯誤。

### 5. WebCodecs API 使用注意事項

本專案使用了 WebCodecs API，該 API 僅在安全上下文（HTTPS 或 localhost）中可用。因此，在部署或測試時，請確保您的網頁在 HTTPS 環境下運行，或者使用 localhost 進行本地測試。

### 6. Thanks
此處重點感謝以下專案，本專案大量使用了以下專案的相關程式碼

- [Project AIRI](https://github.com/moeru-ai/airi)
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
