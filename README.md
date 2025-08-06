# AI Virtual Human - 智能虛擬人系統

> 基於 DH_Live 的高品質虛擬人對話系統，支援雙引擎 TTS 和 Docker 部署

## 🎯 項目概述

AI Virtual Human 是一個完整的智能虛擬人解決方案，整合了先進的語音合成技術和實時人物渲染，為用戶提供自然流暢的對話體驗。

### ✨ 主要特色

- **🎭 高品質虛擬人渲染**：基於 WebGL 的實時人物動畫
- **🎵 雙引擎 TTS 系統**：EdgeTTS + CosyVoice 智能切換
- **🔧 智能音頻處理**：CosyVoice 自動重採樣，確保完美同步
- **🤖 智能對話系統**：支援多種 LLM 服務
- **🐳 Docker 容器化部署**：一鍵啟動完整服務
- **📱 響應式設計**：支援桌面、平板、手機多端適配
- **🔄 自動降級機制**：確保服務穩定性

## 🚀 快速開始

### 前置需求

- Docker 和 Docker Compose
- 至少 4GB 可用記憶體
- 支援 WebGL 的現代瀏覽器

### 一鍵部署

```bash
# 1. 克隆項目
git clone https://github.com/CreateIntelligens/ai-virtual-human-chat

# 2. 配置環境變數
cp .env.sample .env
# 編輯 .env 文件，設置您的 API 密鑰

# 3. 配置 CosyVoice 聲音
cp cosyvoice-service/config/voices.sample.json cosyvoice-service/config/voices.local.json
# 根據需要修改聲音配置

# 4. 配置虛擬人物
cp web_demo/static/avatars/avatars.sample.json web_demo/static/avatars/avatars.json
# 添加您的虛擬人物資源

# 5. 啟動服務
docker-compose up --build
```

### 訪問服務

- **主應用**: http://localhost:8888
- **智能客服聊天室**: http://localhost:8888/static/chat_room_no_watermark.html
- **雙引擎 TTS 測試**: http://localhost:8888/static/dual_tts_chat_room.html
- **API 測試頁面**: http://localhost:8888/static/test_dialog_api.html
- **健康檢查**: http://localhost:8888/health

## 📁 項目結構

```
ai-virtual-human/
├── 📄 README.md                    # 項目說明文檔
├── 🐳 docker-compose.yaml          # Docker Compose 配置
├── 🐳 Dockerfile                   # 主應用容器配置
├── ⚙️ .env.sample                  # 環境配置範例
├── 📋 requirements.txt             # Python 依賴
├── 🚫 .gitignore                   # Git 忽略文件
│
├── 🎵 cosyvoice-service/           # CosyVoice 語音合成服務
│   ├── 🐳 Dockerfile               # CosyVoice 容器配置
│   ├── 📋 requirements.txt         # CosyVoice 依賴
│   ├── 🎛️ config/                  # 聲音配置目錄
│   │   ├── 📄 voices.sample.json   # 聲音配置範例
│   │   └── 🎵 audio_samples/       # 音頻樣本目錄
│   ├── 🧠 cosyvoice/               # CosyVoice 核心程式碼
│   ├── 📦 third_party/             # 第三方依賴
│   └── 🚀 runtime/                 # FastAPI 服務器
│
├── 🎭 web_demo/                    # Web 應用主目錄
│   ├── 🚀 server.py                # FastAPI 主服務器
│   ├── 📄 README.md                # Web 應用說明
│   │
│   ├── 🎵 voiceapi/                # TTS 語音 API 系統
│   │   ├── 🎛️ tts_config_manager.py      # TTS 配置管理器
│   │   ├── 🔄 dual_tts_manager.py         # 雙引擎 TTS 管理器
│   │   ├── 🤖 llm.py                      # LLM 對話接口
│   │   │
│   │   ├── 🎵 tts_engines/               # TTS 引擎實現
│   │   │   ├── 📄 base_tts.py            # 基礎抽象類
│   │   │   ├── 🚀 edge_tts_engine.py     # EdgeTTS 引擎
│   │   │   └── 🎭 cosyvoice_engine.py    # CosyVoice 引擎
│   │   │
│   │   └── ⚙️ tts_configs/               # TTS 配置文件
│   │       ├── 🚀 edge_tts.json          # EdgeTTS 配置
│   │       ├── 🎭 cosyvoice.json         # CosyVoice 配置
│   │       └── 🔗 voice_mapping.json     # 聲音映射配置
│   │
│   └── 🌐 static/                  # 靜態資源目錄
│       ├── 🎭 avatars/             # 虛擬人物資源
│       │   └── 📄 avatars.sample.json    # 人物配置範例
│       ├── 🎨 css/                 # 樣式文件
│       ├── 📜 js/                  # JavaScript 腳本
│       ├── 🖼️ common/              # 公共資源
│       └── 🎪 chat_room_no_watermark.html     # 智能客服聊天室
│
├── 🧠 cosyvoice_models/            # CosyVoice 模型存放目錄
│   └── 📁 trained_models20250801/  # 您的微調模型
│
├── 🎭 data/                        # 人物數據文件
├── 🎬 mini_live/                   # 人物渲染核心
└── 🧠 talkingface/                 # 人臉動畫系統
```

## 🎵 TTS 引擎系統

### 支援的引擎

#### 🚀 EdgeTTS (微軟)
- **優勢**: 快速、穩定、免費
- **聲音**: 甜美女聲、嫵媚女聲、青澀男聲、霸氣男聲
- **適用**: 快速響應場景

#### 🎭 CosyVoice (阿里巴巴)
- **優勢**: 高品質、可定制、支援微調
- **聲音**: 溫柔女聲（艾卡）、沉穩男聲（主播）
- **適用**: 高品質音頻需求
- **🔧 自動重採樣**: 22.05kHz → 16kHz，確保與虛擬人系統完美兼容

### 智能引擎選擇

系統會根據以下策略自動選擇最佳引擎：

1. **用戶指定引擎**: 優先使用用戶選擇的引擎
2. **聲音映射**: 根據聲音 ID 自動選擇對應引擎
3. **自動降級**: 主引擎失敗時切換到備用引擎
4. **負載均衡**: 根據引擎負載智能分配

### 聲音選擇界面

聲音選擇下拉選單按引擎分組顯示：

```
🚀 EdgeTTS (快速)
├── 甜美女聲
├── 嫵媚女聲
├── 青澀男聲
└── 霸氣男聲

🎭 CosyVoice (高品質)
├── 溫柔女聲
└── 沉穩男聲
```

## 🎭 虛擬人物系統

### 人物配置

編輯 `web_demo/static/avatars/avatars.json` 配置虛擬人物：

```json
{
  "default": "male1",
  "avatars": [
    {
      "id": "male1",
      "name": "man",
      "description": "男性角色",
      "path": "/static/avatars/aikka"
    }
  ]
}
```

### 人物資源結構

每個人物需要以下資源：

```
avatars/your_character/
├── 01.mp4                    # 人物視頻
├── combined_data.json.gz     # 人物數據
└── preview.jpg              # 預覽圖片（可選）
```

## 🤖 LLM 對話配置

### 支援的 LLM 服務

系統支援兩種 LLM 服務提供商，在 `.env` 文件中配置：

#### Groq
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

#### Google Gemini
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
```

### 獲取 API 密鑰

#### Groq API
1. 訪問 [Groq Console](https://console.groq.com/)
2. 註冊並登入帳戶
3. 在 API Keys 頁面創建新的 API 密鑰
4. 複製密鑰到 `.env` 文件中

#### Google Gemini API
1. 訪問 [Google AI Studio](https://makersuite.google.com/)
2. 登入 Google 帳戶
3. 創建新的 API 密鑰
4. 複製密鑰到 `.env` 文件中

## 🔧 API 文檔

### TTS API

#### 獲取可用引擎
```http
GET /tts/providers
```

#### 獲取聲音列表
```http
GET /tts/voices
```

#### 生成語音
```http
POST /tts/generate
Content-Type: application/json

{
  "text": "你好，這是測試文本",
  "provider": "cosyvoice",
  "voice_id": "gentle_female"
}
```

#### 流式對話
```http
POST /eb_stream
Content-Type: application/json

{
  "input_mode": "text",
  "prompt": "你好",
  "voice_id": "gentle_female",
  "provider": "cosyvoice"
}
```

### 健康檢查
```http
GET /health
```

## 🛠️ 配置指南

### 環境變數配置

複製 `.env.sample` 為 `.env` 並修改以下配置：

```bash
# TTS 引擎配置
TTS_DEFAULT_PROVIDER=edge_tts
TTS_ENABLED_PROVIDERS=edge_tts,cosyvoice

# CosyVoice 配置
COSYVOICE_ENABLED=true
COSYVOICE_API_URL=http://cosyvoice-service:50001
COSYVOICE_API_TIMEOUT=180

# LLM 配置
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# 或使用 Gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_gemini_api_key_here
# GEMINI_MODEL=gemini-pro
```

### CosyVoice 聲音配置

複製 `cosyvoice-service/config/voices.example.json` 為 `voices.local.json` 並配置：

```json
{
  "voices": [
    {
      "id": "gentle_female",
      "name": "溫柔女聲",
      "prompt_text": "您的提示文本",
      "audio_file": "your_audio_sample.mp3",
      "seed": 112556,
      "description": "聲音描述"
    }
  ]
}
```

### 虛擬人物配置

複製 `web_demo/static/avatars/avatars.sample.json` 為 `avatars.json` 並添加您的人物：

```json
{
  "default": "your_character",
  "avatars": [
    {
      "id": "your_character",
      "name": "您的角色名稱",
      "description": "角色描述",
      "path": "/static/avatars/your_character"
    }
  ]
}
```

## 🎪 使用場景

### 智能客服聊天室

訪問 `http://localhost:8888/static/chat_room_no_watermark.html`

**特色功能**：
- 🎭 實時虛擬人物動畫
- 🎵 智能語音合成
- 📱 響應式設計
- 🔄 自動引擎切換

**使用方法**：
1. 選擇虛擬人物
2. 選擇語音引擎和聲音
3. 輸入問題開始對話




## 🔧 故障排除

### 常見問題

#### 1. CosyVoice 服務無法啟動

**檢查模型路徑**：
```bash
ls -la cosyvoice_models/{你的模型資料夾名稱}
```

**查看容器日誌**：
```bash
docker-compose logs cosyvoice-service
```

#### 2. 聲音生成失敗

**檢查引擎狀態**：
```bash
curl http://localhost:8888/health
```

**檢查聲音配置**：
```bash
curl http://localhost:8888/tts/voices
```

#### 3. 虛擬人物無法載入

**檢查人物資源**：
```bash
ls -la web_demo/static/avatars/your_character/
```

**檢查配置文件**：
```bash
cat web_demo/static/avatars/avatars.json
```

#### 4. 音頻同步問題

**CosyVoice 音頻與虛擬人不同步**：
- 系統已自動啟用重採樣功能，將 22.05kHz 轉換為 16kHz
- 檢查日誌中是否有重採樣成功的訊息：
```bash
docker-compose logs ai-virtual-human | grep "重採樣"
```

**重採樣功能異常**：
- 確認容器內 FFmpeg 可用：
```bash
docker-compose exec ai-virtual-human ffmpeg -version
```

#### 5. 網絡連接問題

**檢查容器網絡**：
```bash
docker network ls
docker-compose ps
```

### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs ai-virtual-human
docker-compose logs cosyvoice-service

# 實時查看日誌
docker-compose logs -f
```

### 性能優化

#### GPU 支援

如果您有 NVIDIA GPU，在 `docker-compose.yaml` 中啟用 GPU 支援：

```yaml
cosyvoice-service:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

#### 記憶體優化

根據您的系統調整記憶體限制：

```yaml
cosyvoice-service:
  deploy:
    resources:
      limits:
        memory: 8G
      reservations:
        memory: 4G
```

## 📈 系統監控

### 健康檢查

系統提供完整的健康檢查端點：

```bash
curl http://localhost:8888/health
```

響應示例：
```json
{
  "status": "healthy",
  "tts_engines": [
    {
      "id": "edge_tts",
      "name": "Microsoft EdgeTTS",
      "status": "available"
    },
    {
      "id": "cosyvoice",
      "name": "CosyVoice",
      "status": "available"
    }
  ],
  "total_engines": 2,
  "available_engines": 2
}
```

### 性能指標

- **引擎可用性**: 實時監控 TTS 引擎狀態
- **響應時間**: 追蹤 API 響應延遲
- **成功率**: 統計請求成功率
- **資源使用**: 監控 CPU 和記憶體使用

## 🔒 安全注意事項

### 生產環境部署

1. **API 限流**: 添加 API 請求限制
2. **輸入驗證**: 驗證用戶輸入內容和長度
3. **HTTPS**: 使用 HTTPS 加密通信
4. **防火牆**: 限制不必要的端口訪問
5. **日誌監控**: 監控異常訪問和錯誤

### 數據隱私

1. **敏感信息**: 不要在日誌中記錄敏感信息
2. **API 密鑰**: 使用環境變數管理 API 密鑰
3. **用戶數據**: 遵循數據保護法規
4. **模型安全**: 保護自定義模型文件

## 🚀 部署選項

### 開發環境

```bash
# 快速啟動（使用預設配置）
docker-compose up
```

### 生產環境

```bash
# 生產環境部署
docker-compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d
```

### 雲端部署

支援部署到以下平台：
- **AWS ECS**: 使用 Fargate 或 EC2
- **Google Cloud Run**: 容器化部署
- **Azure Container Instances**: 快速部署
- **Kubernetes**: 大規模集群部署


### 代碼規範

- 使用 Python PEP 8 代碼風格
- 添加適當的註釋和文檔
- 編寫單元測試
- 遵循項目的目錄結構



## 🙏 致謝

特別感謝以下開源項目：

- **[DH_Live](https://github.com/kleinlee/DH_live)**: 虛擬人渲染核心
- **[EdgeTTS](https://github.com/rany2/edge-tts)**: 微軟語音合成
- **[CosyVoice](https://github.com/FunAudioLLM/CosyVoice)**: 阿里巴巴語音合成
- **[FastAPI](https://fastapi.tiangolo.com/)**: 現代 Python Web 框架
- **[Docker](https://www.docker.com/)**: 容器化平台

---

**© 2025 Create Intelligens Inc. | AI Virtual Human Technology**

> 🌟 如果這個項目對您有幫助，請給我們一個 Star！
