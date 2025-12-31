# 🎯 AI Voice Studio - 智能文字轉語音服務

一個基於 Docker 的 AI 文字轉語音服務，提供現代化的網頁界面和完整的 API 支援。

## ✨ 特色功能

- 🚀 **一鍵部署**: 使用 Docker Compose 快速啟動
- ⚡ **vLLM 加速**: 可選的 vLLM 推理加速，大幅提升生成速度
- 🔥 **自動暖機**: 服務啟動後自動執行測試推理，避免首次請求失敗
- 🎨 **現代化網頁界面**: 響應式設計，支援桌面和手機
- 🎯 **預配置聲音**: 管理員預先設定多種聲音選項
- 🔄 **熱重載**: 修改代碼無需重新構建容器
- 🎛️ **靈活配置**: 通過 JSON 檔案管理聲音配置
- 📱 **簡潔操作**: 只需選擇聲音和輸入文字
- 🎵 **即時播放**: 生成後立即播放和下載音頻

## 📦 快速開始

### 環境需求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA GPU (推薦，用於加速推理)
- NVIDIA Container Toolkit (GPU 支援)

### 🚀 一鍵啟動

```bash
# 進入項目目錄
cd ai-voice-studio

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

### 🌐 訪問服務

- **網頁界面**: http://localhost:8085
- **API 端點**: http://localhost:50005

## ⚙️ 配置說明

### 🔧 環境變數設定

**首次使用前，請先設定環境變數：**

1. 複製環境變數範本：
   ```bash
   cp .env.sample .env
   ```

2. 編輯 `.env` 檔案，設定您的實際配置值：
   ```bash
   nano .env
   # 或使用您偏好的編輯器
   ```

3. 確保模型檔案路徑正確且存在

⚠️ **重要提醒**: `.env` 檔案包含敏感資訊，已加入 `.gitignore` 不會上傳到版本控制。

### 環境變數配置 (.env)

```env
# 模型配置 (請修改為您的實際模型路徑)
MODEL_DIR=./models/your-model-directory/
# 範例: MODEL_DIR=./models/trained_models_naer_20251208/cosyvoice2
# 範例: MODEL_DIR=/path/to/your/models

# 服務端口
PORT=50005
WEB_PORT=8085

# vLLM 加速 (設置為 "true" 啟用, "false" 禁用)
# 注意: vLLM 需要 GPU 支援，可提供顯著的速度提升
# 首次推理: 無 vLLM ~60 秒, 有 vLLM ~1 秒
# 後續推理: 無 vLLM ~10 秒, 有 vLLM ~0.5 秒
ENABLE_VLLM=true

# Docker 項目名稱
COMPOSE_PROJECT_NAME=ai-voice-studio
```

### ⚡ vLLM 加速說明

vLLM 是一個高性能的大語言模型推理引擎，可以大幅提升語音生成速度：

**性能對比**:
- **首次推理**: 
  - 無 vLLM: ~60 秒
  - 有 vLLM: ~1 秒 (首次啟動需額外 50 秒初始化)
- **後續推理**: 
  - 無 vLLM: ~10 秒
  - 有 vLLM: ~0.5 秒

**啟用條件**:
- 需要 NVIDIA GPU (建議 8GB+ 顯存)
- CUDA 12.1+ 支援
- 適用於高頻率使用場景

**啟用方法**:
1. 編輯 `.env` 檔案設置 `ENABLE_VLLM=true`
2. 重啟服務: `docker compose restart`
3. 首次啟動會進行自動暖機，需等待約 2 分鐘

**注意事項**:
- vLLM 初始化需要額外時間 (~50 秒)
- 會佔用更多顯存 (~2GB)
- 如遇到記憶體不足，可設置為 `false` 使用標準模式

### 聲音配置管理

#### 配置檔案說明
- `config/voices.example.json` - 範例配置檔案（提交到 Git）
- `config/voices.local.json` - 您的個人配置（Git 忽略）
- `config/audio_samples/` - 語音樣本目錄

#### 首次設定
1. 複製範例配置：
   ```bash
   cp config/voices.example.json config/voices.local.json
   ```
2. 編輯 `config/voices.local.json` 添加您的聲音配置
3. 將語音樣本檔案放入 `config/audio_samples/` 目錄
4. 重啟服務以載入新配置

#### 聲音配置格式

```json
{
  "voices": [
    {
      "id": "gentle_female",
      "name": "溫柔女聲",
      "prompt_text": "你好，歡迎使用我們的語音服務",
      "audio_file": "gentle_female.wav",
      "seed": 12345,
      "description": "適合客服、朗讀等溫和場景"
    }
  ]
}
```

#### 添加新聲音

1. 將語音樣本檔案放入 `config/audio_samples/` 目錄
2. 在 `config/voices.local.json` 中添加對應配置
3. 重啟服務：`docker-compose restart ai-voice-studio`

#### 配置檔案自動選擇
系統會自動選擇配置檔案：
- 如果存在 `voices.local.json`，優先使用個人配置
- 如果不存在，則使用 `voices.example.json` 範例配置
- 啟動時會在日誌中顯示使用的配置檔案

## 📁 目錄結構

```
ai-voice-studio/
├── README.md              # 本說明文件
├── .env                   # 環境變數配置
├── .gitignore            # Git 忽略檔案
├── .dockerignore         # Docker 忽略檔案
├── docker-compose.yaml   # Docker Compose 配置
├── Dockerfile            # Docker 映像檔配置
├── nginx.conf            # Nginx 配置
├── start.sh              # 容器啟動腳本
├── warmup.py             # 自動暖機腳本
├── requirements.txt      # Python 依賴
├── config/               # 配置檔案目錄
│   ├── voices.example.json  # 範例配置檔案
│   ├── voices.local.json    # 個人配置檔案（Git 忽略）
│   └── audio_samples/       # 語音樣本目錄
├── web/                  # 網頁界面
│   ├── index.html        # 主頁面
│   ├── style.css         # 樣式檔案
│   └── script.js         # JavaScript 邏輯
├── cosyvoice/            # AI 引擎核心代碼
│   ├── cli/              # 命令行介面
│   ├── vllm/             # vLLM 整合模組
│   └── ...               # 其他模組
├── models/               # 模型檔案目錄
├── runtime/              # 運行時檔案
│   └── python/fastapi/   # FastAPI 服務
└── third_party/          # 第三方依賴
```

## 🎨 網頁功能

### 主要功能
- **聲音選擇**: 從預配置的聲音類型中選擇
- **文字輸入**: 支援最多 500 字元的文字轉語音
- **即時播放**: 生成完成後立即播放音頻
- **下載功能**: 一鍵下載生成的音頻檔案

### 支援格式
- **輸入音頻**: WAV, MP3, FLAC 等常見格式
- **輸出音頻**: WAV 格式 (22.05kHz, 16-bit)
- **檔案大小**: 語音樣本建議小於 10MB

## 🚀 API 使用

### 主要端點

#### GET /api/voices

獲取可用的聲音配置列表。

**回應範例**:
```json
{
  "voices": [
    {
      "id": "gentle_female",
      "name": "溫柔女聲",
      "description": "適合客服、朗讀等溫和場景"
    }
  ]
}
```

#### POST /api/inference_with_voice_config

使用預配置聲音進行語音合成。

**請求參數**:
```
tts_text: 要轉換的文字 (必填)
voice_id: 聲音配置 ID (必填)
```

**請求範例**:
```bash
curl -X POST http://localhost:50005/inference_with_voice_config \
  -F "tts_text=你好，這是一個測試" \
  -F "voice_id=gentle_female" \
  --output output.wav
```

**回應**: WAV 格式音頻檔案

### 其他可用端點

- `POST /inference_zero_shot_wav`: 原始 Zero-shot 模式 (需上傳音頻)
- `POST /inference_sft`: SFT 模式語音合成
- `POST /inference_cross_lingual`: 跨語言語音合成
- `POST /inference_instruct`: 指令式語音合成

## 🛠️ 開發指南

### 本地開發

```bash
# 進入容器進行除錯
docker-compose exec ai-voice-studio bash

# 查看服務狀態
docker-compose ps

# 重啟特定服務
docker-compose restart ai-voice-studio
```

### 代碼修改

由於使用了 volume 掛載，您可以直接修改本地檔案：

- **網頁檔案**: `web/` 目錄下的檔案修改後立即生效
- **配置檔案**: 修改 `config/voices.local.json` 後需重啟容器
- **Python 代碼**: 修改後需重啟容器

### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs ai-voice-studio

# 即時跟蹤日誌
docker-compose logs -f
```

## 🔧 進階配置

### 自動暖機功能

系統在啟動後會自動執行一次測試推理，確保：
- 模型完全載入
- GPU 記憶體預分配
- 首次用戶請求不會超時

**暖機流程**:
1. 等待服務啟動 (約 50-120 秒)
2. 檢查服務健康狀態
3. 執行一次測試語音生成
4. 完成後系統即可正常服務

**日誌查看**:
```bash
# 查看暖機日誌
docker logs ai-voice-studio-app 2>&1 | grep -A 10 "Running warmup"
```

**跳過暖機** (不推薦):
如需跳過自動暖機，可修改 `start.sh` 註解掉暖機部分。

### Volume 掛載說明

本項目使用 Volume 掛載實現熱重載：

```yaml
volumes:
  - .:/opt/CosyVoice  # 整個項目目錄掛載到容器
```

**優點**:
- 修改代碼立即生效（部分檔案需重啟）
- 無需重新構建映像
- 方便開發除錯

**需重啟的修改**:
- Python 代碼 (`cosyvoice/`, `runtime/`)
- 配置檔案 (`config/voices.local.json`)
- 啟動腳本 (`start.sh`)

**立即生效的修改**:
- 網頁檔案 (`web/`)
- 靜態資源

### GPU 支援

確保已安裝 NVIDIA Container Toolkit：

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 端口修改

修改 `.env` 檔案中的端口設定：

```env
PORT=8000          # API 端口
WEB_PORT=3000      # 網頁端口
```

### 記憶體優化

對於記憶體較小的系統，可以調整 Docker 配置：

```yaml
# docker-compose.yaml
services:
  ai-voice-studio:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

## 📝 故障排除

### 常見問題

#### 1. 容器啟動失敗
```bash
# 檢查日誌
docker-compose logs ai-voice-studio

# 檢查端口占用
netstat -tulpn | grep :50005
```

#### 2. GPU 不可用
```bash
# 檢查 GPU 狀態
nvidia-smi

# 檢查 Docker GPU 支援
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### 3. 聲音配置載入失敗
- 確認 `config/voices.local.json` 或 `config/voices.example.json` 格式正確
- 檢查語音樣本檔案是否存在於 `config/audio_samples/`
- 確認檔案路徑和檔名匹配

#### 4. 網頁無法訪問
- 檢查防火牆設定
- 確認端口映射正確
- 檢查 Nginx 配置

#### 5. vLLM 啟動失敗
```bash
# 檢查 GPU 顯存
nvidia-smi

# 查看詳細錯誤
docker logs ai-voice-studio-app 2>&1 | grep -i error

# 常見問題:
# - 顯存不足: 設置 ENABLE_VLLM=false
# - transformers 版本衝突: 已在 requirements.txt 鎖定版本
# - MKL threading 衝突: 已在環境變數中修復
```

#### 6. 首次推理失敗或超時
- 這是正常現象，因為首次推理需要載入模型
- **解決方案**: 系統已內建自動暖機功能
- 等待暖機完成後 (~2 分鐘) 再進行操作
- 查看日誌確認暖機是否完成: `docker logs ai-voice-studio-app | grep "System is fully warmed up"`

#### 7. 權限問題
```bash
# 如遇到 start.sh 權限錯誤
chmod +x start.sh

# 重啟容器
docker compose restart
```

### 性能優化

#### 1. 啟用 vLLM 加速
```env
# .env 檔案
ENABLE_VLLM=true
```
顯著提升推理速度，適合高頻使用場景。

#### 2. 模型載入優化
```env
# 使用 SSD 存儲模型
MODEL_DIR=/fast-storage/models/your-model-directory/
```

#### 3. 記憶體優化
```bash
# 清理未使用的 Docker 資源
docker system prune -a

# 調整 Docker 記憶體限制
# 編輯 docker-compose.yaml
deploy:
  resources:
    limits:
      memory: 12G  # 根據實際情況調整
```

#### 4. 顯存優化
- 不使用 vLLM: ~6GB 顯存
- 使用 vLLM: ~8GB 顯存
- 如顯存不足，設置 `ENABLE_VLLM=false`

#### 5. 網路優化
```yaml
# docker-compose.yaml 中添加
networks:
  ai-voice-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🔬 技術細節

### vLLM 整合

本項目整合了 vLLM 加速引擎，主要技術特點：

**自定義模型註冊**:
- 實現了 `CosyVoice2ForCausalLM` 自定義模型
- 自動註冊到 vLLM ModelRegistry
- 位於 `cosyvoice/vllm/cosyvoice2.py`

**環境修復**:
- 修復 DeepSpeed CUDA 檢查問題
- 修復 MKL threading layer 衝突
- 修復 transformers 版本相容性

**依賴版本**:
```txt
vllm==0.9.0
transformers==4.51.3  # 鎖定版本以確保相容
torch==2.7.0
```

### Docker 優化策略

**映像構建優化**:
- 只 COPY 必要的安裝檔案 (requirements.txt, nginx.conf)
- 應用程式代碼通過 volume 掛載
- 無需為代碼修改重新構建映像

**Runtime 生成**:
- gRPC 檔案在 runtime 時生成
- 支援 proto 檔案熱更新

**環境變數隔離**:
- DeepSpeed 操作禁用
- CUDA 環境設定
- MKL threading 配置

### 自動暖機機制

**實現方式**:
- `warmup.py` 腳本自動執行
- 使用健康檢查端點確認服務狀態
- 執行實際推理請求預熱模型

**好處**:
- 避免用戶首次請求超時
- 預分配 GPU 資源
- 確保服務完全就緒

## 📊 系統要求

### 最低配置
- CPU: 4 核心
- RAM: 8GB
- GPU: NVIDIA GPU 6GB+ 顯存 (無 vLLM)
- 硬碟: 20GB 可用空間

### 推薦配置
- CPU: 8 核心+
- RAM: 16GB+
- GPU: NVIDIA GPU 8GB+ 顯存 (有 vLLM)
- 硬碟: 50GB+ SSD

### 支援的 GPU
- NVIDIA RTX 系列 (RTX 3060+)
- NVIDIA Tesla 系列
- NVIDIA A 系列
- CUDA 12.1+ 相容的任何 GPU


## 🙏 致謝

本項目基於以下開源項目構建：

- **CosyVoice**: [Apache License 2.0](https://github.com/FunAudioLLM/CosyVoice) - 提供核心 AI 語音合成技術
- **vLLM**: [Apache License 2.0](https://github.com/vllm-project/vllm) - 高性能 LLM 推理引擎
- **FastAPI**: 高性能 Web 框架
- **Docker**: 容器化部署方案

感謝開源社群的貢獻，讓 AI 技術更加普及和易用。

## 📝 更新日誌

### v1.1.0 (2025-12-11)
- ✨ 新增 vLLM 加速支援，推理速度提升 10-20 倍
- 🔥 新增自動暖機功能，避免首次請求失敗
- 🐛 修復 DeepSpeed CUDA 檢查問題
- 🐛 修復 MKL threading layer 衝突
- 🐛 修復 transformers 版本相容性問題
- 📦 優化 Docker 構建流程，支援熱重載
- 📚 完善文件說明和故障排除指南

### v1.0.0 (初始版本)
- 🚀 基礎語音合成功能
- 🎨 網頁界面
- 📝 聲音配置管理
- 🔧 Docker 部署支援



---

**享受 AI 語音合成的樂趣！** 🎉
