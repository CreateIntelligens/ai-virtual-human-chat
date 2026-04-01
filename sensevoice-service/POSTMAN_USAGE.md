# SenseVoice ASR API - Postman 使用指南

## 快速開始

### 方法一：導入 Postman Collection（推薦）

1. 打開 Postman
2. 點擊左上角的 **Import** 按鈕
3. 選擇 `SenseVoice_ASR_API.postman_collection.json` 文件
4. 導入成功後，您會在左側看到 "SenseVoice ASR API" 集合

### 方法二：手動創建請求

## 詳細步驟

### 1. 基本 ASR 請求設置

#### 創建新請求
1. 點擊 Postman 左上角的 **New** → **HTTP Request**
2. 設置請求方法為 **POST**
3. 輸入 URL: `http://localhost:8000/api/v1/asr`

#### 配置 Body（重要）
1. 選擇 **Body** 標籤
2. 選擇 **form-data** 選項（不是 raw 或 binary）
3. 添加以下字段：

| Key | Type | Value | 說明 |
|-----|------|-------|------|
| files | File | [選擇文件] | 點擊右側下拉選單選擇 **File**，然後點擊 **Select Files** 上傳音頻 |
| keys | Text | `audio.wav` | 音頻文件的名稱（可自定義） |
| lang | Text | `auto` | 語言選項：auto, zh, en, yue, ja, ko |

#### 發送請求
點擊 **Send** 按鈕，在下方可以看到返回結果

### 2. 不同語言的配置

#### 中文（普通話）
```
files: [選擇音頻文件]
keys: chinese_audio.wav
lang: zh
```

#### 英文
```
files: [選擇音頻文件]
keys: english_audio.wav
lang: en
```

#### 粵語
```
files: [選擇音頻文件]
keys: cantonese_audio.wav
lang: yue
```

#### 日文
```
files: [選擇音頻文件]
keys: japanese_audio.wav
lang: ja
```

#### 韓文
```
files: [選擇音頻文件]
keys: korean_audio.wav
lang: ko
```

### 3. 上傳多個音頻文件

在 form-data 中：

1. 添加多個 `files` 欄位（Key 名稱都是 `files`）
2. 每個都選擇 **File** 類型並上傳不同的文件
3. `keys` 欄位用逗號分隔：`audio1.wav,audio2.wav,audio3.wav`

具體配置：
```
files: [第一個音頻文件] (Type: File)
files: [第二個音頻文件] (Type: File)
files: [第三個音頻文件] (Type: File)
keys: audio1.wav,audio2.wav,audio3.wav (Type: Text)
lang: auto (Type: Text)
```

### 4. 查看 GPU 記憶體狀態

#### 創建 GET 請求
- Method: **GET**
- URL: `http://localhost:8000/memory`
- 點擊 **Send**

返回示例：
```json
{
    "gpu_available": true,
    "allocated_gb": 2.45,
    "cached_gb": 3.12,
    "total_gb": 24.0,
    "usage_percent": 10.21,
    "device_name": "NVIDIA GeForce RTX 3090"
}
```

### 5. 手動清理 GPU 記憶體

#### 創建 POST 請求
- Method: **POST**
- URL: `http://localhost:8000/memory/cleanup`
- 不需要 Body
- 點擊 **Send**

## 返回結果說明

成功的 ASR 請求會返回：

```json
{
    "result": [
        {
            "key": "audio.wav",
            "text": "辨識後的完整文字（繁體中文，包含情感標記）",
            "raw_text": "原始辨識的文字（繁體中文）",
            "clean_text": "清理後的文字（繁體中文，移除所有標記）"
        }
    ]
}
```

### 字段說明
- **text**: 經過後處理的完整文字，包含情感標記等資訊
- **raw_text**: 模型原始輸出的文字
- **clean_text**: 移除所有特殊標記的純文字

## 常見問題

### 1. 錯誤：422 Unprocessable Entity
**原因**: 參數格式不正確
**解決**: 
- 確保在 Body 中選擇了 **form-data**（不是 raw）
- 確保 `files` 的 Type 選擇為 **File**
- 確保 `keys` 和 `lang` 的 Type 選擇為 **Text**

### 2. 錯誤：Connection refused
**原因**: 服務未啟動
**解決**: 
```bash
cd /home/hank/DH_live/ai-virtual-human/sensevoice-service
python api.py
```

### 3. 沒有返回結果或結果為空
**原因**: 音頻文件格式不支援或音頻內容無語音
**解決**:
- 確保音頻是 WAV 或 MP3 格式
- 音頻採樣率建議為 16KHz
- 確認音頻中有清晰的語音內容

### 4. 如何修改服務端口
如果服務運行在其他端口，修改 URL 中的端口號：
```
http://localhost:8000 → http://localhost:YOUR_PORT
```

## 環境變量設置

如果需要使用特定 GPU：
```bash
export SENSEVOICE_DEVICE=cuda:1
python api.py
```

## 音頻格式建議

- **格式**: WAV 或 MP3
- **採樣率**: 16000 Hz（推薦）
- **聲道**: 單聲道或立體聲（會自動轉換為單聲道）
- **長度**: 建議不超過 30 秒（單個文件）

## 測試工作流程

1. **啟動服務** → 訪問 `http://localhost:8000/` 確認服務運行
2. **檢查記憶體** → GET `http://localhost:8000/memory`
3. **執行 ASR** → POST `http://localhost:8000/api/v1/asr` 上傳音頻
4. **查看結果** → 檢查返回的 JSON 數據
5. **清理記憶體** → POST `http://localhost:8000/memory/cleanup`（可選）

## 訪問 API 文檔

在瀏覽器中訪問：`http://localhost:8000/docs`

這會打開 FastAPI 自動生成的 Swagger UI，可以在網頁中直接測試所有 API。
