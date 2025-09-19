# 自定義詞庫功能說明

## 概述

本 TTS 服務已加入自定義詞庫功能，可以在文本轉語音之前自動將特定詞彙進行替換轉換。

## Speaker 配置

Speaker 配置檔案位於：`assets/speaker.json`

### 新格式（推薦）

```json
{
    "hayley": {
        "audio_paths": [
            "assets/voices/hayley/Hayley正常說開場白.mp3"
        ],
        "default_seed": 8
    },
    "speaker2": {
        "audio_paths": [
            "assets/voices/speaker2/voice1.wav",
            "assets/voices/speaker2/voice2.wav"
        ],
        "default_seed": 42
    }
}
```

### 舊格式（仍支援）

```json
{
    "hayley": [
        "assets/voices/hayley/Hayley正常說開場白.mp3"
    ]
}
```

### Seed 優先級

1. **API 請求中的 seed** - 最高優先級
2. **Speaker 配置中的 default_seed** - 中等優先級
3. **系統預設 seed (8)** - 最低優先級

## 詞庫檔案

詞庫檔案位於：`custom_dict.json`

### 格式範例

```json
{
    "三立": "(三立)",
    "AI": "人工智慧",
    "API": "應用程式介面",
    "TTS": "語音合成",
    "JSON": "傑森格式"
}
```

### 格式說明

- 檔案格式：JSON
- 編碼：UTF-8
- 結構：鍵值對，其中鍵是原始詞彙，值是要替換的詞彙
- 轉換是完全匹配替換（case-sensitive）

## API 端點

### 詞庫管理

#### 1. 獲取詞庫狀態
```
GET /dict_status
```

回應範例：
```json
{
    "status": "success",
    "dict_count": 5,
    "dictionary": {
        "三立": "(三立)",
        "AI": "人工智慧"
    }
}
```

#### 2. 重新載入詞庫
```
POST /reload_dict
```

回應範例：
```json
{
    "status": "success",
    "message": "詞庫重新載入成功，共 5 個詞條",
    "dict_count": 5
}
```

### TTS 端點（已自動整合詞庫功能）

所有 TTS 端點都會自動應用詞庫轉換，並支援 `seed` 參數來控制生成的隨機性：

1. **`POST /tts`** - 使用預設角色
   ```json
   {
     "text": "要轉換的文字",
     "character": "角色名稱",
     "seed": 8  // 可選，未提供時使用 speaker 的 default_seed
   }
   ```

2. **`POST /tts_url`** - 使用自定義音頻檔案
   ```json
   {
     "text": "要轉換的文字", 
     "audio_paths": ["音頻檔案路徑"],
     "seed": 8  // 可選，預設值為 8
   }
   ```

3. **`POST /audio/speech`** - OpenAI 兼容端點
   ```json
   {
     "input": "要轉換的文字",
     "voice": "角色名稱",
     "model": "模型名稱",
     "seed": 8  // 可選，未提供時使用 speaker 的 default_seed
   }
   ```

4. **`POST /tts_upload`** - 上傳音頻檔案
   - Form data: `text`, `audio_file`, `seed`

#### Seed 參數說明
- **型別**: 整數 (int)
- **預設值**: 8
- **作用**: 控制語音生成的隨機性，相同的 seed 值會產生相同的語音輸出
- **用途**: 確保可重現的語音生成結果

## 使用流程

1. **編輯詞庫檔案**
   ```bash
   nano custom_dict.json
   ```

2. **重新載入詞庫**（無需重啟服務）
   ```bash
   curl -X POST http://localhost:11996/reload_dict
   ```

3. **使用 TTS API**
   - 發送的文本會自動根據詞庫進行轉換
   - 轉換過程會在控制台輸出日誌

## 範例

### 轉換範例

輸入文本：`"三立新聞台報導 AI 技術進展"`
轉換後：`"(三立)新聞台報導 人工智慧 技術進展"`

### 測試腳本

執行測試腳本來驗證功能：
```bash
python test_custom_dict.py
```

## 注意事項

1. **詞庫載入時機**：服務啟動時自動載入，也可透過 API 手動重新載入
2. **轉換順序**：按照詞庫中的順序依次進行替換
3. **匹配規則**：完全匹配（區分大小寫）
4. **性能影響**：詞庫較大時可能略微影響 TTS 回應時間
5. **檔案編碼**：請確保 `custom_dict.json` 使用 UTF-8 編碼
6. **錯誤處理**：如果詞庫檔案格式錯誤，服務會繼續運行但不會應用轉換

## 調試

- 查看控制台輸出來確認詞庫載入狀態
- 文本轉換時會輸出轉換前後的對比
- 使用 `/dict_status` 端點檢查當前詞庫內容
