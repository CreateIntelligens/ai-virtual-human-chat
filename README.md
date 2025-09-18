# AI Virtual Human - 智能虛擬人系統

> 基於 DH_Live 的高品質虛擬人對話系統，支援三引擎 TTS 和 Docker 部署

## 🎯 項目概述

AI Virtual Human 是一個完整的智能虛擬人解決方案，整合了先進的語音合成技術和實時人物渲染，為用戶提供自然流暢的對話體驗。

### ✨ 主要特色

- 🎭 **高品質虛擬人渲染** - 基於 WebGL 的實時人物動畫
- 🎤 **VAD 智能語音檢測** - 自動檢測說話結束並停止錄音
- 🎨 **語音輸入對話** - SenseVoice STT 支援中文語音識別
- 📝 **智能文字後處理** - 自動處理中文標點符號優化
- 🎵 **三引擎 TTS 系統** - EdgeTTS + CosyVoice + IndexTTS 智能切換
- 🔬 **語音克隆技術** - IndexTTS 支援基於參考音頻的語音克隆
- 🤖 **智能對話系統** - 支援多種 LLM 服務
- 🐳 **Docker 容器化部署** - 一鍵啟動完整服務
- 📱 **響應式設計** - 支援桌面、平板、手機多端適配
- 🔄 **完整對話流程** - 語音輸入 → STT → LLM → TTS → 虛擬人播放
- 🎯 **統一 UI 設計** - 專業的紫藍色主題配色
- 🔧 **健壯錯誤處理** - 完善的容錯機制和狀態重置

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

## 🎤 語音輸入功能

### 🎯 功能特色
- **🎤 VAD 智能語音檢測** - 自動檢測說話結束並停止錄音
- **🎨 一鍵語音對話** - 點擊麥克風按鈕即可開始語音輸入
- **📝 智能文字後處理** - 自動處理中文標點符號優化
- **🔄 實時語音識別** - 基於 SenseVoice 的高精度中文 STT
- **🎯 完整對話流程** - 語音輸入 → STT → LLM → TTS → 虛擬人播放
- **📱 響應式設計** - 支援桌面和手機的語音輸入
- **🔧 健壯錯誤處理** - 完善的容錯機制和狀態重置

### 🎯 VAD 智能語音檢測

**核心特色：**
- **自動停止錄音** - 檢測到 1.5 秒靜音後自動停止
- **實時音量分析** - 使用 Web Audio API 分析音頻頻譜
- **智能語音判斷** - 區分語音、噪音和靜音
- **可配置參數** - 語音閾值、靜音時間、錄音時長限制
- **安全機制** - 最小錄音時間保護、最大錄音時間限制

**技術實現：**
```javascript
// VAD 配置參數
const VAD_CONFIG = {
    VOICE_THRESHOLD: 25,        // 語音檢測閾值 (0-255)
    SILENCE_DURATION: 1500,     // 靜音持續時間 (毫秒)
    MIN_RECORDING_TIME: 500,    // 最小錄音時間 (毫秒)
    MAX_RECORDING_TIME: 30000,  // 最大錄音時間 (毫秒)
    ANALYSIS_INTERVAL: 100      // 分析間隔 (毫秒)
};
```

**智能對話流程：**
1. **🎤 點擊麥克風** → 開始錄音，顯示"等待語音"
2. **🗣️ 開始說話** → VAD 檢測到語音，顯示"檢測到語音"
3. **⏸️ 停止說話** → 開始靜音倒數，顯示"即將自動停止"
4. **🤖 自動停止** → 1.5秒後自動停止錄音並處理
5. **🎤 語音識別** → SenseVoice 識別 + 智能文字後處理
6. **💬 顯示結果** → 用戶訊息顯示在聊天區
7. **🤖 AI 回應** → LLM 生成回應 + TTS 語音合成
8. **🎵 播放語音** → 虛擬人物說話 + 音頻播放

### 📝 智能文字後處理

**功能特色：**
- **中文句號處理** - 自動將純句號 "。" 轉換為英文點號 "."
- **結尾句號移除** - 移除文字結尾的中文句號，避免重複標點
- **標點符號優化** - 智能處理語音識別結果的標點符號
- **文字清理** - 去除多餘空格和格式化字符

**處理邏輯：**
```javascript
// 智能文字後處理示例
"你好。" → "你好"           // 移除結尾句號
"。" → "."                 // 純句號轉換
"謝謝你" → "謝謝你"         // 無變化
```

### 🔧 SenseVoice STT 配置

**環境變數配置：**
```bash
# SenseVoice STT 配置
SENSEVOICE_ENABLED=true
SENSEVOICE_API_URL=http://sensevoice-service:50002
SENSEVOICE_API_TIMEOUT=30
```

**技術特色：**
- **多語言支援** - 中文、英文、粵語、日語、韓語
- **高精度識別** - 針對中文優化的語音識別模型
- **實時處理** - 低延遲的語音轉文字處理
- **自動降噪** - 內建回音消除和噪音抑制

### 📱 語音對話使用指南

#### 桌面版操作
1. 點擊聊天輸入框左側的 🎤 麥克風按鈕
2. 允許瀏覽器訪問麥克風權限
3. 看到錄音指示器後開始說話
4. 再次點擊按鈕停止錄音
5. 系統自動進行語音識別和對話處理

#### 手機版操作
1. 點擊底部輸入區域的 🎤 按鈕
2. 允許瀏覽器麥克風權限
3. 對著手機麥克風清晰說話
4. 點擊停止按鈕結束錄音
5. 等待語音識別和 AI 回應

#### 語音輸入最佳實踐
- **清晰發音** - 保持正常語速，發音清晰
- **安靜環境** - 選擇較安靜的環境進行錄音
- **適當距離** - 保持與麥克風 15-30cm 的距離
- **完整句子** - 說完整的句子，避免過短的詞語

## 🎵 三引擎 TTS 系統架構

### 🏗️ 系統架構特色

我們的三引擎TTS系統採用了先進的微服務架構，實現了高可用性和智能引擎選擇：

- **🔄 智能引擎切換** - 根據聲音ID自動選擇最適合的TTS引擎
- **⚡ 並行處理** - 多引擎同時初始化，提升系統響應速度
- **🛡️ 容錯機制** - 單一引擎故障不影響其他引擎正常工作
- **📊 統一配置管理** - 集中式配置管理，支援動態配置更新
- **🎯 前端智能顯示** - 聲音選項按引擎分組，用戶體驗優化

### 🚀 EdgeTTS（微軟）
- **優勢**: 快速、穩定、免費
- **聲音**: 甜美女聲、嫵媚女聲、青澀男聲、霸氣男聲
- **適用**: 快速響應場景
- **配置**: 無需額外配置，開箱即用
- **端口**: 內建於主服務，無需獨立端口

### 🎭 CosyVoice（阿里巴巴）
- **優勢**: 可定制、支援微調、台語支援
- **聲音**: 溫柔女聲、專業男聲（可自定義）
- **適用**: 台語生成、個性化語音需求
- **配置**: 需要模型文件和聲音配置
- **端口**: 50001
- **模型**: 支援自定義微調模型

### 🔬 IndexTTS（語音克隆）
- **優勢**: 語音克隆、VLLM加速、高度定制
- **聲音**: Hayley開心活潑、主播男聲、Cindy（可自定義）
- **適用**: 個性化語音需求、語音克隆
- **配置**: 基於VLLM的高性能推理
- **端口**: 8001
- **特色**: 基於參考音頻自動克隆聲音

### 🎤 SenseVoice（語音識別）
- **優勢**: 高精度中文識別、多語言支援
- **適用**: 語音輸入對話場景
- **配置**: 自動模型下載，無需手動配置
- **端口**: 50002
- **特色**: 專為中文優化的 STT 引擎

### 🔧 最新系統修復 (2025年1月)

我們最近完成了重大的系統優化，解決了多個關鍵問題：

#### ✅ TTS引擎初始化修復
- **CosyVoice引擎**: 修正了配置路徑錯誤，現在可以正確讀取API配置
- **IndexTTS引擎**: 修復了健康檢查超時設置和環境變數端口衝突問題
- **統一配置管理**: 實現了provider_info.api_config的標準化配置結構

#### ✅ 前端界面優化
- **聲音列表排序**: 修復了localeCompare方法對undefined值的處理錯誤
- **IndexTTS聲音顯示**: 添加了缺失的display_name字段，解決聲音選項空白問題
- **引擎分組顯示**: 聲音選項按引擎類型分組，提升用戶體驗

#### ✅ 網路連接優化
- **容器間通信**: 確保所有TTS服務之間的網路連接穩定
- **健康檢查**: 實現了robust的健康檢查機制，支援aiohttp.ClientTimeout
- **端口配置**: 統一了環境變數和配置文件的端口設置

#### 🎯 系統狀態確認
```bash
# 檢查所有引擎狀態
curl http://localhost:8888/tts/providers

# 預期輸出：三個引擎全部可用
✅ EdgeTTS 引擎已啟用
✅ CosyVoice 引擎已啟用  
✅ IndexTTS 引擎已啟用
🎯 TTS 引擎初始化完成，共啟用 3 個引擎: ['edge_tts', 'cosyvoice', 'indextts']
```

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

### 語音轉文字
```bash
curl -X POST "http://localhost:8888/stt/transcribe" \
  -F "file=@audio.wav"
```

### 語音對話（STT + LLM + TTS）
```bash
curl -X POST "http://localhost:8888/voice_chat" \
  -F "file=@audio.wav" \
  -F "voice_id=female-tianmei" \
  -F "provider=edge_tts"
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

### 健康檢查（包含 STT 狀態）
```bash
curl http://localhost:8888/health
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

### Q: 語音輸入無法使用？

**檢查麥克風權限：**
1. 確認瀏覽器已允許麥克風權限
2. 檢查系統麥克風設置
3. 嘗試重新整理頁面並重新授權

**檢查 SenseVoice 服務：**
```bash
# 檢查服務狀態
docker-compose logs sensevoice-service

# 檢查服務健康狀態
curl http://localhost:50002/
```

### Q: 語音識別準確度低？

**優化錄音環境：**
1. 選擇安靜的環境
2. 保持適當的麥克風距離（15-30cm）
3. 說話清晰，語速適中
4. 避免方言或口音過重

**檢查音頻格式：**
- 確保瀏覽器支援 WebM 或 MP4 音頻格式
- 檢查麥克風採樣率設置

### Q: 語音對話延遲過高？

**優化網絡連接：**
1. 檢查網絡延遲
2. 確保 Docker 容器間通信正常
3. 調整 STT 超時設置

**調整配置：**
```bash
# 在 .env 中調整超時設置
SENSEVOICE_API_TIMEOUT=15  # 降低超時時間
```

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
- **[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)**: 阿里巴巴語音識別

---

**© 2025 Create Intelligens Inc. | AI Virtual Human Technology**

> 🌟 如果這個項目對您有幫助，請給我們一個 Star！
