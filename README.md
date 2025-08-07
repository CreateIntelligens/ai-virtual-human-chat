# AI Virtual Human - 智能虛擬人系統

> 基於 DH_Live 的高品質虛擬人對話系統，支援三引擎 TTS 和 Docker 部署

## 🎯 項目概述

AI Virtual Human 是一個完整的智能虛擬人解決方案，整合了先進的語音合成技術和實時人物渲染，為用戶提供自然流暢的對話體驗。

### ✨ 主要特色

- 🎭 **高品質虛擬人渲染** - 基於 WebGL 的實時人物動畫
- 🎵 **三引擎 TTS 系統** - EdgeTTS + CosyVoice + IndexTTS 智能切換
- 🔬 **語音克隆技術** - IndexTTS 支援基於參考音頻的語音克隆
- 🤖 **智能對話系統** - 支援多種 LLM 服務
- 🐳 **Docker 容器化部署** - 一鍵啟動完整服務
- 📱 **響應式設計** - 支援桌面、平板、手機多端適配

## 🚀 詳細部署指南

### 前置需求

- Docker 和 Docker Compose
- 至少 4GB 可用記憶體
- 支援 WebGL 的現代瀏覽器

### 📁 項目文件結構

部署前請了解項目的文件結構，這將幫助您正確放置模型和配置文件：

```
ai-virtual-human/
├── 📄 README.md                    # 項目說明文檔
├── 🐳 docker-compose.yaml          # Docker Compose 配置
├── ⚙️ .env                         # 環境配置（需要創建）
│
├── 🎵 cosyvoice-service/           # CosyVoice 語音合成服務
│   ├── 🎵 models/                  # CosyVoice 模型存放目錄
│   │   └── [您的模型文件夾]/        # 放置您的 CosyVoice 微調模型
│   └── 🎛️ config/                  # 聲音配置目錄
│       ├── 📄 voices.local.json    # 聲音配置（需要創建）
│       └── 🎵 audio_samples/       # 參考音頻文件目錄
│
├── 🔬 indextts-service/            # IndexTTS 語音克隆服務
│   ├── 📁 checkpoints/             # IndexTTS 模型存放目錄
│   └── 🎛️ config/                  # 聲音配置目錄
│       ├── 📄 voices.json          # 聲音配置（需要創建）
│       └── 🎵 audio_samples/       # 參考音頻文件目錄
│
└── 🎭 web_demo/static/avatars/     # 虛擬人物資源
    ├── 📄 avatars.json             # 人物配置（需要創建）
    └── [您的人物文件夾]/            # 虛擬人物資源文件
```

### 📋 一步步部署流程

#### 步驟 1: 克隆項目

```bash
git clone https://github.com/CreateIntelligens/ai-virtual-human-chat
cd ai-virtual-human-chat
```

#### 步驟 2: 配置環境變數

```bash
# 複製環境配置範例
cp .env.sample .env

# 編輯 .env 文件
nano .env
```

**重要配置項目：**

```bash
# LLM 配置（必須）
LLM_PROVIDER=groq                    # 或 gemini
GROQ_API_KEY=your_groq_api_key_here  # 從 https://console.groq.com/ 獲取
GROQ_MODEL=llama-3.1-70b-versatile

# TTS 引擎配置
TTS_DEFAULT_PROVIDER=edge_tts
TTS_ENABLED_PROVIDERS=edge_tts,cosyvoice,indextts

# CosyVoice 配置
COSYVOICE_ENABLED=true
COSYVOICE_API_URL=http://cosyvoice-service:50001

# IndexTTS 配置
INDEXTTS_ENABLED=true
INDEXTTS_API_URL=http://indextts-service:6008
```

#### 步驟 3: 準備 CosyVoice 模型和聲音（可選）

如果您有 CosyVoice 微調模型：

```bash
# 1. 將您的模型文件夾放入 cosyvoice-service/models/
# 例如：cosyvoice-service/models/my_trained_model/

# 2. 配置聲音文件
cp cosyvoice-service/config/voices.sample.json cosyvoice-service/config/voices.local.json

# 3. 編輯聲音配置
nano cosyvoice-service/config/voices.local.json
```

**聲音配置格式：**

```json
{
  "voices": [
    {
      "id": "my_voice",
      "name": "我的聲音",
      "prompt_text": "這是一段提示文本",
      "audio_file": "my_sample.wav",
      "seed": 112556,
      "description": "聲音描述"
    }
  ]
}
```

**音頻文件要求：**
- 格式：WAV, MP3
- 長度：3-10 秒
- 品質：清晰、無雜音
- 放置位置：`cosyvoice-service/config/audio_samples/`

#### 步驟 4: 準備 IndexTTS 聲音（可選）

```bash
# 1. 配置聲音文件
cp indextts-service/config/voices.sample.json indextts-service/config/voices.json

# 2. 編輯聲音配置
nano indextts-service/config/voices.json
```

**IndexTTS 聲音配置格式：**

```json
{
  "voices": [
    {
      "id": "custom_voice",
      "name": "自定義聲音",
      "audio_file": "reference.wav",
      "description": "基於參考音頻的語音克隆"
    }
  ]
}
```

**參考音頻要求：**
- 格式：WAV（推薦）
- 採樣率：16kHz 或 22.05kHz
- 長度：5-30 秒
- 內容：清晰的語音，最好包含多種音調
- 放置位置：`indextts-service/config/audio_samples/`

#### 步驟 5: 準備虛擬人物資源

```bash
# 1. 配置人物文件
cp web_demo/static/avatars/avatars.sample.json web_demo/static/avatars/avatars.json

# 2. 編輯人物配置
nano web_demo/static/avatars/avatars.json
```

**人物配置格式：**

```json
{
  "default": "my_character",
  "avatars": [
    {
      "id": "my_character",
      "name": "我的角色",
      "description": "角色描述",
      "path": "/static/avatars/my_character"
    }
  ]
}
```

**人物資源結構：**

```
web_demo/static/avatars/my_character/
├── 01.mp4                    # 人物視頻文件（必須）
├── combined_data.json.gz     # 人物數據文件（必須）
└── preview.jpg              # 預覽圖片（可選）
```

#### 步驟 6: 啟動服務

```bash
# 構建並啟動所有服務
docker-compose up --build

# 或在背景運行
docker-compose up --build -d
```

#### 步驟 7: 訪問應用

服務啟動後，您可以訪問：

- **主應用**: http://localhost:8888
- **智能客服聊天室**: http://localhost:8888/static/chat_room_no_watermark.html
- **API 文檔**: http://localhost:8888/docs
- **健康檢查**: http://localhost:8888/health

## 🎵 TTS 引擎說明

### 🚀 EdgeTTS（微軟）
- **優勢**: 快速、穩定、免費
- **聲音**: 甜美女聲、嫵媚女聲、青澀男聲、霸氣男聲
- **適用**: 快速響應場景
- **配置**: 無需額外配置，開箱即用

### 🎭 CosyVoice（阿里巴巴）
- **優勢**: 可定制、支援微調
- **適用**: 台語生成需求
- **配置**: 需要模型文件和聲音配置
- **模型**: 支援自定義微調模型

### 🔬 IndexTTS（語音克隆）
- **優勢**: 語音克隆、高度定制
- **適用**: 個性化語音需求
- **配置**: 需要參考音頻文件
- **特色**: 基於參考音頻自動克隆聲音

## 🔧 API 使用

### 獲取聲音列表
```bash
curl http://localhost:8888/tts/voices
```

### 生成語音
```bash
curl -X POST "http://localhost:8888/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，這是測試文本",
    "provider": "edge_tts",
    "voice_id": "female-tianmei"
  }'
```

### 流式對話
```bash
curl -X POST "http://localhost:8888/eb_stream" \
  -H "Content-Type: application/json" \
  -d '{
    "input_mode": "text",
    "prompt": "你好",
    "voice_id": "female-tianmei"
  }'
```

## 🛠️ 常見問題

### Q: 如何獲取 API 密鑰？

**Groq API:**
1. 訪問 [Groq Console](https://console.groq.com/)
2. 註冊並登入帳戶
3. 在 API Keys 頁面創建新的 API 密鑰

**Google Gemini API:**
1. 訪問 [Google AI Studio](https://makersuite.google.com/)
2. 登入 Google 帳戶
3. 創建新的 API 密鑰

### Q: CosyVoice 服務無法啟動？

**檢查模型路徑：**
```bash
ls -la cosyvoice-service/models/
```

**查看容器日誌：**
```bash
docker-compose logs cosyvoice-service
```

### Q: 虛擬人物無法載入？

**檢查人物資源：**
```bash
ls -la web_demo/static/avatars/your_character/
```

**確認必要文件：**
- `01.mp4` - 人物視頻
- `combined_data.json.gz` - 人物數據

### Q: 聲音生成失敗？

**檢查引擎狀態：**
```bash
curl http://localhost:8888/health
```

**檢查聲音配置：**
```bash
curl http://localhost:8888/tts/voices
```

### Q: IndexTTS 模型下載失敗？

IndexTTS 會在首次啟動時自動下載模型，如果下載失敗：

1. 檢查網絡連接
2. 重啟容器會自動重試
3. 查看容器日誌了解詳情

## 🔒 生產環境注意事項

1. **API 限流**: 添加 API 請求限制
2. **輸入驗證**: 驗證用戶輸入內容和長度
3. **HTTPS**: 使用 HTTPS 加密通信
4. **防火牆**: 限制不必要的端口訪問
5. **數據隱私**: 遵循數據保護法規

## 🙏 致謝

特別感謝以下開源項目：

- **[DH_Live](https://github.com/kleinlee/DH_live)**: 虛擬人渲染核心
- **[EdgeTTS](https://github.com/rany2/edge-tts)**: 微軟語音合成
- **[CosyVoice](https://github.com/FunAudioLLM/CosyVoice)**: 阿里巴巴語音合成
- **[IndexTTS](https://github.com/index-tts/index-tts)**: 語音克隆技術

---

**© 2025 Create Intelligens Inc. | AI Virtual Human Technology**

> 🌟 如果這個項目對您有幫助，請給我們一個 Star！
