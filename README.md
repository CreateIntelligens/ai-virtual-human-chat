# 創造智能 AI 客服聊天室系統

基於 DH_Live 項目的專業 AI 客服聊天室系統，整合了 Groq LLaMA 3.3 70B 模型、虛擬人物渲染、語音合成和智能對話功能。

## 🎯 系統概述

這是一個完整的 AI 客服解決方案，具備：

- **智能對話**: Groq LLaMA 3.3 70B 驅動的高質量對話
- **虛擬人物**: WebGL 驅動的 3D 人物動畫渲染
- **語音合成**: Edge-TTS 整合，支援多種中文語音
- **嘴部同步**: WebAssembly 驅動的精確嘴部動畫
- **響應式設計**: 支援桌面、平板和手機設備
- **專業客服**: 制式回答和身份保護機制

## ⚠️ 重要配置說明

### 🔧 人物配置設置

**首次使用前，請務必完成以下配置：**

1. **複製範例配置**：
   ```bash
   cp web_demo/static/avatars/avatars.sample.json web_demo/static/avatars/avatars.json
   ```

2. **添加您的人物資料**：
   - 將人物資料夾放入 `web_demo/static/avatars/`
   - 更新 `avatars.json` 配置

3. **文件結構**：
   ```
   web_demo/static/avatars/
   ├── avatars.json          # 您的配置文件 (需要創建)
   ├── avatars.sample.json   # 範例配置文件
   ├── your_character1/      # 您的人物資料夾
   │   ├── 01.mp4
   │   └── combined_data.json.gz
   └── your_character2/
       ├── 01.mp4
       └── combined_data.json.gz
   ```

**⚠️ 注意**: 如果沒有正確配置 `avatars.json`，系統會顯示錯誤警示而不是使用預設人物。

## 🚀 快速開始

### 環境要求

- Docker
- Docker Compose
- 8888 端口可用

### 配置 LLM API

編輯 `.env` 文件，選擇並配置您的 LLM 提供商：

**使用 Groq (推薦)：**
```env
# LLM 提供商選擇
LLM_PROVIDER=groq

# Groq API 配置
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

**使用 Gemini：**
```env
# LLM 提供商選擇
LLM_PROVIDER=gemini

# Gemini API 配置
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

### 一鍵啟動

```bash
# 克隆項目
git clone <your-repo-url>
cd ai-virtual-human

# 配置人物 (重要!)
cp web_demo/static/avatars/avatars.sample.json web_demo/static/avatars/avatars.json

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

### 訪問聊天室

- **標準聊天室**：http://localhost:8888/static/chat_room.html
- **去水印版**：http://localhost:8888/static/chat_room_no_watermark.html

## 📁 項目結構

```
ai-virtual-human/
├── .gitignore                    # Git 忽略文件
├── .env                          # 環境配置文件
├── README.md                     # 本文檔
├── docker-compose.yaml           # Docker 配置
├── Dockerfile                    # Docker 鏡像
├── requirements.txt              # Python 依賴
└── web_demo/
    ├── server.py                 # FastAPI 後端服務器
    ├── voiceapi/
    │   └── llm.py               # Groq LLM 整合模組
    └── static/
        ├── chat_room.html        # 標準聊天室頁面
        ├── chat_room_no_watermark.html  # 去水印版聊天室
        ├── js/
        │   ├── MiniLive2.js      # 標準版 JavaScript
        │   └── MiniLive2_v2.js   # 去水印版 JavaScript
        ├── common/               # 共用資源
        └── avatars/
            ├── avatars.json      # 人物配置文件 (需要創建)
            ├── avatars.sample.json  # 範例配置文件
            └── your_characters/  # 您的人物資料夾
```

## 🎭 人物管理

### 人物配置文件

`web_demo/static/avatars/avatars.json` 控制所有可用人物：

```json
{
  "default": "your_character",
  "avatars": [
    {
      "id": "your_character",
      "name": "您的角色名稱",
      "description": "角色描述",
      "path": "avatars/your_character",
      "gender": "male/female",
      "tags": ["標籤1", "標籤2"]
    }
  ]
}
```

### 添加新人物

1. **創建人物資料夾**:
   ```bash
   mkdir web_demo/static/avatars/new_character
   ```

2. **添加必要文件**:
   ```
   web_demo/static/avatars/new_character/
   ├── 01.mp4                    # 人物視頻文件
   └── combined_data.json.gz     # 模型數據文件
   ```

3. **更新配置文件**:
   在 `avatars.json` 中添加新人物配置

4. **重啟服務**:
   ```bash
   docker-compose restart
   ```

### 文件格式要求

- **01.mp4**: H.264 編碼的 MP4 視頻文件
- **combined_data.json.gz**: Gzip 壓縮的 JSON 模型數據
- 建議視頻解析度: 512x512 或更高
- 建議幀率: 25-30 FPS

## 🎨 聊天室功能

### 🤖 智能對話系統

#### LLM 驅動
- **Groq LLaMA 3.3 70B** 提供高質量對話
- **專業客服提示詞** 確保專業服務體驗
- **制式回答** 針對常見問題提供標準回應

#### 身份保護
系統嚴格維護客服專員身份：
- 被問及身份時回應："我是創造智能的客服專員"
- 專業的客服語氣和用詞
- 絕不透露 AI 本質

### 📚 制式回答系統

針對常見問題提供標準回應：

| 問題類型 | 觸發關鍵字 | 標準回應 |
|---------|-----------|---------|
| 產品介紹 | "產品介紹", "服務" | 介紹五大服務類型 |
| 公司介紹 | "公司介紹", "你們是誰" | 創造智能公司簡介 |
| AIGC影片 | "aigc", "影片" | AIGC影片服務詳情 |
| 智能客服 | "智能客服", "客服" | 智能客服解決方案 |
| MCN聯盟 | "mcn", "聯盟" | MCN聯盟服務介紹 |
| LINE CRM | "line", "crm" | LINE CRM功能說明 |
| AI虛擬人 | "虛擬人", "數位人" | AI虛擬人技術介紹 |

### 🎵 語音配置

系統支援多種 Edge-TTS 語音：

| 語音ID | 顯示名稱 | Edge-TTS語音 | 適用性別 |
|--------|----------|--------------|----------|
| male-qn-qingse | 青澀男 | zh-CN-YunxiNeural | 男性 |
| male-qn-badao | 霸氣男 | zh-CN-YunyangNeural | 男性 |
| wumei_yujie | 嫵媚女 | zh-CN-XiaoxiaoNeural | 女性 |
| female-tianmei | 甜美女 | zh-CN-XiaoyiNeural | 女性 |

### 📱 響應式設計

#### 桌面版 (≥769px)
- 左右分割布局
- 虛擬人物在左側，聊天區域在右側
- 完整的控制面板和功能

#### 平板版 (769px-1024px)
- 垂直堆疊布局
- 虛擬人物在上方，聊天區域在下方
- 適配觸控操作

#### 手機版 (≤768px)
- 全螢幕沉浸式設計
- 透明聊天覆蓋層
- 毛玻璃效果
- 聊天區域避免遮擋人物臉部

## 🔧 技術架構

### 後端技術棧
- **FastAPI** 高性能 Web 框架
- **Groq API** LLaMA 3.3 70B 模型
- **Edge-TTS** 微軟語音合成
- **Docker** 容器化部署

### 前端技術棧
- **WebGL** 3D 人物渲染
- **WebAssembly** 高性能計算
- **Web Audio API** 音頻處理
- **現代 CSS** 響應式設計

### 核心流程
```
用戶輸入 → LLM處理 → 文本分割 → TTS合成 → 音頻播放 → 人物動畫
```

## 🖥️ 使用教學

### 基本操作

1. **選擇人物**: 在下拉選單選擇想要的虛擬人物
2. **選擇語音**: 在下拉選單選擇語音類型
3. **輸入對話**: 在文字框輸入想說的話
4. **發送對話**: 點擊"發送"按鈕或按 Enter 鍵
5. **觀看效果**: 人物會說話並做出相應的嘴部動作

### 鍵盤快捷鍵

- **Enter**: 發送對話
- **Shift + Enter**: 換行（在文字框中）

## ⚙️ 環境變數

可在 `.env` 文件中配置：

```env
# LLM 提供商選擇
LLM_PROVIDER=groq

# Groq API 配置
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# 服務端口
PORT=8888
```

## 🐛 故障排除

### 常見問題

**Q: 人物配置載入失敗**
A: 
1. 確認 `avatars.json` 文件存在
2. 檢查文件格式是否正確
3. 確認人物資料夾完整
4. 參考 `avatars.sample.json` 範例

**Q: Groq API 調用失敗**
A: 檢查 `.env` 文件中的 `GROQ_API_KEY` 是否正確配置

**Q: 虛擬人物無法載入**
A: 
1. 確認人物資料夾存在且包含必要文件
2. 檢查瀏覽器控制台錯誤
3. 確認 WebAssembly 模組載入成功

**Q: 語音合成失敗**
A: 
1. 檢查 Edge-TTS 服務狀態
2. 確認音頻權限已開啟
3. 查看容器日誌: `docker-compose logs`

**Q: 聊天室無法訪問**
A: 
1. 確認 Docker 容器正在運行
2. 檢查端口 8888 未被占用
3. 查看防火牆設置

### 日誌查看

```bash
# 查看實時日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs ai-virtual-human

# 查看最近50行日誌
docker-compose logs --tail=50
```

### 重置系統

```bash
# 停止服務
docker-compose down

# 清理容器和鏡像
docker-compose down --rmi all

# 重新構建和啟動
docker-compose up --build -d
```

## 🔄 開發指南

### 本地開發

1. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```

2. **配置人物**:
   ```bash
   cp web_demo/static/avatars/avatars.sample.json web_demo/static/avatars/avatars.json
   ```

3. **啟動開發服務器**:
   ```bash
   cd web_demo
   python server.py
   ```

4. **訪問開發環境**:
   - 標準版: http://localhost:8888/static/chat_room.html
   - 去水印版: http://localhost:8888/static/chat_room_no_watermark.html

### 代碼結構

- `server.py`: 主要後端邏輯
- `voiceapi/llm.py`: LLM 整合模組
- `static/chat_room.html`: 標準聊天室界面
- `static/chat_room_no_watermark.html`: 去水印版聊天室
- `static/js/MiniLive2.js`: 標準版前端核心邏輯
- `static/js/MiniLive2_v2.js`: 去水印版前端邏輯
- `static/avatars/`: 人物資源管理

### 添加新功能

1. **後端 API**: 在 `server.py` 中添加新端點
2. **前端邏輯**: 在相應的 JS 文件中實現
3. **界面元素**: 在 HTML 中添加 UI 組件
4. **測試**: 確保功能正常運作

### 自定義配置

#### 修改客服提示詞
編輯 `voiceapi/llm.py` 中的 `CUSTOMER_SERVICE_PROMPT` 變數。

#### 添加新的制式回答
在 `get_standard_response()` 函數中添加新的關鍵字匹配規則。

#### 調整語音設置
在 HTML 文件中修改 `voiceDropdown` 的選項。

## 🔄 降級機制

系統具備完善的降級機制：

- **API 失敗處理** 自動切換到標準回應
- **網路錯誤恢復** 友善的錯誤提示
- **服務連續性** 確保客服不中斷
- **配置錯誤警示** 明確的錯誤提示和解決方案

## 📝 更新日誌

### v3.0.0 (當前版本)
- ✅ 整合專業 AI 客服功能
- ✅ 新增響應式聊天室設計
- ✅ 添加去水印版本
- ✅ 完善錯誤處理機制
- ✅ 優化人物配置管理
- ✅ 改進 Git 配置和文檔

### v2.0.0
- ✅ 重構為靜態人物配置系統
- ✅ 移除複雜的動態 API 依賴
- ✅ 新增人物配置 JSON 管理
- ✅ 優化目錄結構
- ✅ 完善 Docker 化部署

### v1.0.0
- ✅ 基礎對話功能
- ✅ Edge-TTS 整合
- ✅ WebAssembly 嘴部動畫
- ✅ Docker 容器化

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本項目
2. 創建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交 Pull Request

## 📄 許可證

本項目基於原始 DH_Live 項目修改，請遵循相應的開源許可證。

## 🙏 致謝

- 原始 DH_Live 項目團隊
- Groq 和 LLaMA 模型
- Edge-TTS 項目
- WebAssembly 社群
- Docker 社群

---

**享受與 AI 虛擬客服的專業對話體驗！** 🎉

**創造智能科技股份有限公司**  
專業的 Martech 行銷科技解決方案提供商
