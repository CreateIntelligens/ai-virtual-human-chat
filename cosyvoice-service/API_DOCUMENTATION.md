# AI Voice Studio — 完整 API 文件

本文件說明 AI Voice Studio 前端頁面所使用的全部 API，包含架構說明、端點規格、呼叫範例，讓您在**任何專案外部環境**都能完整重現相同功能。

---

## 目錄

1. [系統架構概覽](#1-系統架構概覽)
2. [服務部署資訊](#2-服務部署資訊)
3. [API 端點總覽](#3-api-端點總覽)
4. [CosyVoice TTS API（主要語音合成）](#4-cosyvoice-tts-api主要語音合成)
   - [GET /voices — 取得聲音列表](#41-get-voices--取得聲音列表)
   - [POST /inference\_with\_voice\_config — 聲音配置推論](#42-post-inference_with_voice_config--聲音配置推論)
   - [POST /inference\_zero\_shot — 零樣本推論](#43-post-inference_zero_shot--零樣本推論)
   - [POST /inference\_zero\_shot\_wav — 零樣本推論（回傳 WAV）](#44-post-inference_zero_shot_wav--零樣本推論回傳-wav)
   - [POST /inference\_sft — SFT 微調推論](#45-post-inference_sft--sft-微調推論)
   - [POST /inference\_cross\_lingual — 跨語言推論](#46-post-inference_cross_lingual--跨語言推論)
   - [POST /inference\_instruct — 指令式推論](#47-post-inference_instruct--指令式推論)
5. [外部 TTS API（IndexTTS）](#5-外部-tts-apiindextts)
6. [台語翻譯 API](#6-台語翻譯-api)
7. [前端頁面完整流程說明](#7-前端頁面完整流程說明)
8. [聲音配置檔案格式](#8-聲音配置檔案格式)
9. [完整呼叫範例（Python）](#9-完整呼叫範例python)
10. [完整呼叫範例（curl）](#10-完整呼叫範例curl)
11. [完整呼叫範例（JavaScript / Node.js）](#11-完整呼叫範例javascript--nodejs)
12. [錯誤處理](#12-錯誤處理)
13. [注意事項](#13-注意事項)

---

## 1. 系統架構概覽

```
使用者瀏覽器
    │
    ▼
Nginx (port 8085)
    ├─ /                  → 靜態前端 (index.html / script.js)
    ├─ /api/              → FastAPI CosyVoice 後端 (localhost:50001)
    ├─ /config/audio_samples/ → 靜態音頻樣本檔案
    └─ /external-tts/     → 外部 IndexTTS 服務 (10.9.0.35:8011)

翻譯服務（外部第三方）
    └─ https://learn-language.tokyo/taigiTranslator/model2/translate
```

前端產生**兩個並行語音版本**：

| 版本 | 流程 |
|------|------|
| 版本 1 | 輸入文字 → **台語翻譯 API** → CosyVoice 零樣本 TTS |
| 版本 2 | 輸入文字 → **IndexTTS 外部服務**（直接生成） |

---

## 2. 服務部署資訊

| 服務 | 對外端口 | 說明 |
|------|----------|------|
| Nginx Web 伺服器 | `8085` | 前端靜態頁面 + API 反向代理 |
| FastAPI CosyVoice | `50001` | CosyVoice 語音合成後端 |
| IndexTTS 外部服務 | `10.9.0.35:8011` | 外部角色聲音 TTS |

> **從外部直接呼叫時**，建議直接打 FastAPI 端口 `50001`，或透過 Nginx `8085` 的 `/api/` 路徑。

---

## 3. API 端點總覽

| 方法 | 路徑（透過 Nginx） | 路徑（直連 FastAPI） | 功能 |
|------|-------------------|---------------------|------|
| GET | `/api/voices` | `/voices` | 取得聲音配置列表 |
| POST | `/api/inference_with_voice_config` | `/inference_with_voice_config` | 使用預設聲音配置合成語音 |
| POST | `/api/inference_zero_shot` | `/inference_zero_shot` | 上傳音頻樣本零樣本合成 |
| POST | `/api/inference_zero_shot_wav` | `/inference_zero_shot_wav` | 上傳音頻樣本零樣本合成（完整 WAV） |
| POST | `/api/inference_sft` | `/inference_sft` | SFT 預訓練說話人合成 |
| POST | `/api/inference_cross_lingual` | `/inference_cross_lingual` | 跨語言語音合成 |
| POST | `/api/inference_instruct` | `/inference_instruct` | 指令式合成（SFT 說話人） |
| POST | `/external-tts/tts` | `http://10.9.0.35:8011/tts` | IndexTTS 角色語音合成 |

---

## 4. CosyVoice TTS API（主要語音合成）

**Base URL（透過 Nginx）：** `http://10.9.0.35:8085/api`  
**Base URL（直連 FastAPI）：** `http://10.9.0.35:50001`

---

### 4.1 GET /voices — 取得聲音列表

取得目前可用的所有聲音配置（讀取 `config/voices.local.json` 或 `voices.example.json`）。

**請求**

```
GET /voices
```

無需任何參數。

**回應（200 OK）**

```json
{
  "voices": [
    {
      "id": "gentle_female",
      "name": "溫柔女聲",
      "prompt_text": "嗨～我是創造智能的AI代言人艾卡！想知道你的 MBTI 是哪一型嗎？還是對我們的 AI 服務好奇？我都可以告訴你～快來跟我聊聊吧!",
      "audio_file": "Hayley開心說開場白.mp3",
      "seed": 6,
      "description": "適合客服、朗讀等溫和場景"
    },
    {
      "id": "professional_male",
      "name": "沉穩男聲",
      "prompt_text": "是砸了八千億，就是希望呢來到這個地方，可以讓民眾飽覽美景，而且呢甚至這八千萬飽覽美景的。",
      "audio_file": "anchorman1_4_1070748_1426635.wav",
      "seed": 671112,
      "description": "商務簡報、新聞播報等正式場合"
    }
  ]
}
```

| 欄位 | 型態 | 說明 |
|------|------|------|
| `id` | string | 呼叫 TTS API 時使用的聲音識別碼 |
| `name` | string | 聲音顯示名稱 |
| `prompt_text` | string | 音頻樣本的對應文字逐字稿 |
| `audio_file` | string | 音頻樣本檔案名稱（存放於 `config/audio_samples/`） |
| `seed` | integer | 隨機種子（影響生成結果一致性） |
| `description` | string | 聲音用途描述 |

---

### 4.2 POST /inference\_with\_voice\_config — 聲音配置推論

**前端「版本 1」使用此端點**（台語翻譯後的文字送入此處）。

使用伺服器預先配置好的聲音樣本進行零樣本語音合成，不需要自己上傳音頻參考檔案。

**請求**

- **Content-Type:** `multipart/form-data`

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 要合成的文字（台語羅馬字 / 中文皆可） |
| `voice_id` | ✅ | string | 聲音識別碼（來自 `/voices` 的 `id` 欄位） |
| `original_text` | ❌ | string | 原始輸入文字（僅供後端日誌記錄，不影響合成） |

**回應（200 OK）**

- **Content-Type:** `audio/wav`
- **Body:** WAV 音頻二進位資料
- **音頻規格：**
  - 採樣率：22050 Hz
  - 聲道數：1（單聲道）
  - 位元深度：16-bit PCM

**回應標頭範例**

```
Content-Type: audio/wav
Content-Disposition: attachment; filename=gentle_female_output.wav
```

---

### 4.3 POST /inference\_zero\_shot — 零樣本推論

上傳自訂音頻參考檔案進行零樣本 TTS，回傳**串流（chunked streaming）**音頻。

**請求**

- **Content-Type:** `multipart/form-data`

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 要合成的文字 |
| `prompt_text` | ✅ | string | 音頻樣本的文字逐字稿（需與 `prompt_wav` 一致） |
| `prompt_wav` | ✅ | file | 參考音頻檔案（16kHz 單聲道 WAV 為佳） |
| `seed` | ❌ | integer | 隨機種子（預設 0） |

**回應（200 OK）**

- **Content-Type:** `audio/wav`（串流）
- 回傳的是**原始 PCM 片段串流**（非完整 WAV 檔頭），適合即時播放

> ⚠️ 注意：此端點回傳串流的裸 PCM 資料，若要儲存為 WAV 需自行加上 WAV 檔頭。若需完整 WAV 檔，請使用 `/inference_zero_shot_wav`。

---

### 4.4 POST /inference\_zero\_shot\_wav — 零樣本推論（回傳 WAV）

與 `inference_zero_shot` 功能相同，但回傳**完整 WAV 格式**檔案，適合直接存檔。

**請求**

同 `inference_zero_shot`（同樣的 `multipart/form-data` 參數）。

**回應（200 OK）**

- **Content-Type:** `audio/wav`
- 回傳完整 WAV 檔（含正確檔頭），可直接儲存或播放
- **音頻規格：** 22050 Hz、單聲道、16-bit PCM

---

### 4.5 POST /inference\_sft — SFT 微調推論

使用模型內建的預訓練說話人（Speaker Fine-Tuned）進行語音合成，**不需要**上傳音頻樣本。

**請求**

- **Content-Type:** `multipart/form-data`

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 要合成的文字 |
| `spk_id` | ✅ | string | 說話人 ID（模型內建，依模型版本而異） |

**回應（200 OK）**

- 串流 PCM 音頻資料

---

### 4.6 POST /inference\_cross\_lingual — 跨語言推論

保留說話人音色的同時合成不同語言，適合「用中文母語者聲音說英文」等情境。

**請求**

- **Content-Type:** `multipart/form-data`

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 目標語言的文字 |
| `prompt_wav` | ✅ | file | 說話人參考音頻（16kHz WAV） |

**回應（200 OK）**

- 串流 PCM 音頻資料

---

### 4.7 POST /inference\_instruct — 指令式推論

透過自然語言指令（如「用慢速說話」「用激動的語氣」）控制語音合成風格（CosyVoice2 功能）。

**v1 版本參數（使用 SFT 說話人）：**

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 要合成的文字 |
| `spk_id` | ✅ | string | 說話人 ID |
| `instruct_text` | ✅ | string | 風格指令（中文自然語言描述） |

**v2 版本（上傳音頻 + 指令）：**

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `tts_text` | ✅ | string | 要合成的文字 |
| `instruct_text` | ✅ | string | 風格指令 |
| `prompt_wav` | ✅ | file | 參考音頻 |

---

## 5. 外部 TTS API（IndexTTS）

**前端「版本 2」使用此端點**（直接使用原文，不經過翻譯）。

**Base URL（透過 Nginx）：** `http://10.9.0.35:8085/external-tts`  
**Base URL（直連）：** `http://10.9.0.35:8011`

---

### POST /tts

使用角色音色（Character）直接生成語音。

**請求**

- **Content-Type:** `application/json`

```json
{
  "text": "要合成的文字內容",
  "character": "gentle_female",
  "seed": 6
}
```

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `text` | ✅ | string | 要合成的文字 |
| `character` | ✅ | string | 角色識別碼（與 CosyVoice 的 `voice_id` 相同） |
| `seed` | ❌ | integer | 隨機種子（預設依聲音配置的 `seed` 值，前端取自 `voiceConfig.seed`，無值則用 `2`） |

**回應（200 OK）**

- **Content-Type:** `audio/wav` 或其他音頻格式
- Body：音頻二進位資料

---

## 6. 台語翻譯 API

**前端用於生成「版本 1」之前的文字翻譯步驟。**

**Base URL：** `https://learn-language.tokyo`

---

### POST /taigiTranslator/model2/translate

將繁體中文翻譯成台語（台羅拼音或漢字台語）。

**請求**

- **Content-Type:** `application/json`

```json
{
  "inputText": "這是一個好日子！你吃飽了嗎？",
  "inputLan": "Traditional Chinese:zhTW",
  "outputLan": "Taiwanese:tw"
}
```

| 參數 | 必填 | 型態 | 說明 |
|------|------|------|------|
| `inputText` | ✅ | string | 原始繁體中文文字 |
| `inputLan` | ✅ | string | 輸入語言，固定為 `"Traditional Chinese:zhTW"` |
| `outputLan` | ✅ | string | 輸出語言，固定為 `"Taiwanese:tw"` |

**回應（200 OK）**

```json
{
  "outputText": "這是一個好日仔！你食飽矣無？"
}
```

> 📝 回傳的是**台文漢字**（非羅馬拼音），可直接作為 CosyVoice 台語 TTS 的輸入文字。

| 欄位 | 說明 |
|------|------|
| `outputText` | 翻譯後的台語文字（前端從此欄位取值，若無則 fallback 使用 `result` 欄位，再 fallback 使用原文） |

---

## 7. 前端頁面完整流程說明

```
使用者
  │
  ├─ 頁面載入
  │     └─ GET /api/voices
  │           └─ 填充聲音下拉選單，自動選取第一個選項
  │
  ├─ 填入文字 + 選擇聲音 + 按下「生成語音」
  │
  ├─ [並行執行，互不等待]
  │
  ├─ 版本 1 流程：
  │     ├─ POST https://learn-language.tokyo/taigiTranslator/model2/translate
  │     │     body: { inputText, inputLan: "Traditional Chinese:zhTW", outputLan: "Taiwanese:tw" }
  │     └─ POST /api/inference_with_voice_config
  │           body (multipart): { tts_text: <台語文字>, voice_id, original_text: <原文> }
  │           回傳 WAV → 建立 Blob URL → 設定 <audio> 播放器
  │
  └─ 版本 2 流程：
        └─ POST /external-tts/tts
              body (JSON): { text: <原文>, character: <voice_id>, seed: <voiceConfig.seed 或 2> }
              回傳音頻 → 建立 Blob URL → 設定 <audio> 播放器
```

---

## 8. 聲音配置檔案格式

`config/voices.local.json`（本機環境）或 `config/voices.example.json`（範例）：

```json
{
  "voices": [
    {
      "id": "gentle_female",
      "name": "溫柔女聲",
      "prompt_text": "嗨～我是創造智能的AI代言人艾卡！想知道你的 MBTI 是哪一型嗎？還是對我們的 AI 服務好奇？我都可以告訴你～快來跟我聊聊吧!",
      "audio_file": "Hayley開心說開場白.mp3",
      "seed": 6,
      "description": "適合客服、朗讀等溫和場景"
    },
    {
      "id": "professional_male",
      "name": "沉穩男聲",
      "prompt_text": "是砸了八千億，就是希望呢來到這個地方，可以讓民眾飽覽美景，而且呢甚至這八千萬飽覽美景的。",
      "audio_file": "anchorman1_4_1070748_1426635.wav",
      "seed": 671112,
      "description": "商務簡報、新聞播報等正式場合"
    }
  ]
}
```

音頻樣本放置路徑：`config/audio_samples/<audio_file>`

支援格式：`.wav`、`.mp3`（伺服器會透過 `load_wav` 以 16kHz 讀取）

---

## 9. 完整呼叫範例（Python）

### 9.1 取得聲音列表

```python
import requests

BASE_URL = "http://10.9.0.35:8085/api"  # 透過 Nginx
# 或直連: BASE_URL = "http://10.9.0.35:50001"

response = requests.get(f"{BASE_URL}/voices")
voices = response.json()

for voice in voices["voices"]:
    print(f"ID: {voice['id']}, 名稱: {voice['name']}, 描述: {voice['description']}")
```

---

### 9.2 使用聲音配置合成語音（版本 1 流程）

```python
import requests

BASE_URL = "http://10.9.0.35:8085/api"

def translate_to_taiwanese(text: str) -> str:
    """將繁體中文翻譯成台語"""
    response = requests.post(
        "https://learn-language.tokyo/taigiTranslator/model2/translate",
        json={
            "inputText": text,
            "inputLan": "Traditional Chinese:zhTW",
            "outputLan": "Taiwanese:tw"
        }
    )
    data = response.json()
    return data.get("outputText") or data.get("result") or text

def generate_audio_with_translation(text: str, voice_id: str, output_path: str):
    """翻譯 → 合成語音 → 儲存 WAV"""
    # Step 1: 翻譯成台語
    translated_text = translate_to_taiwanese(text)
    print(f"翻譯結果: {translated_text}")

    # Step 2: 呼叫 CosyVoice 合成
    response = requests.post(
        f"{BASE_URL}/inference_with_voice_config",
        data={
            "tts_text": translated_text,
            "voice_id": voice_id,
            "original_text": text  # 可選，僅供日誌記錄
        }
    )
    response.raise_for_status()

    # Step 3: 儲存 WAV
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"語音已儲存至: {output_path}")

# 使用範例
generate_audio_with_translation(
    text="這是一個好日子！你吃飽了嗎？",
    voice_id="gentle_female",
    output_path="output_v1.wav"
)
```

---

### 9.3 使用 IndexTTS 直接合成語音（版本 2 流程）

```python
import requests

NGINX_URL = "http://10.9.0.35:8085"
# 或直連外部服務: EXTERNAL_TTS_URL = "http://10.9.0.35:8011"

def generate_audio_direct(text: str, character: str, seed: int = 2, output_path: str = "output_v2.wav"):
    """直接使用 IndexTTS 合成語音"""
    response = requests.post(
        f"{NGINX_URL}/external-tts/tts",
        json={
            "text": text,
            "character": character,
            "seed": seed
        }
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"語音已儲存至: {output_path}")

# 使用範例
generate_audio_direct(
    text="這是一個好日子！你吃飽了嗎？",
    character="gentle_female",
    seed=6,
    output_path="output_v2.wav"
)
```

---

### 9.4 上傳自訂音頻樣本（零樣本推論）

```python
import requests

BASE_URL = "http://10.9.0.35:50001"  # 直連 FastAPI

def zero_shot_tts(tts_text: str, prompt_text: str, prompt_wav_path: str, output_path: str, seed: int = 42):
    """使用自訂音頻樣本進行零樣本語音合成"""
    with open(prompt_wav_path, "rb") as wav_file:
        response = requests.post(
            f"{BASE_URL}/inference_zero_shot_wav",
            data={
                "tts_text": tts_text,
                "prompt_text": prompt_text,
                "seed": seed
            },
            files={
                "prompt_wav": ("prompt.wav", wav_file, "audio/wav")
            }
        )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"語音已儲存至: {output_path}")

# 使用範例
zero_shot_tts(
    tts_text="你好，歡迎使用 AI 語音合成系統。",
    prompt_text="這是我的聲音示範，請根據這段錄音來複製我的音色。",
    prompt_wav_path="my_voice_sample.wav",
    output_path="cloned_voice_output.wav",
    seed=42
)
```

---

### 9.5 同時執行兩個版本（完整重現前端邏輯）

```python
import requests
import concurrent.futures

BASE_URL = "http://10.9.0.35:8085/api"
NGINX_URL = "http://10.9.0.35:8085"

def translate_to_taiwanese(text: str) -> str:
    resp = requests.post(
        "https://learn-language.tokyo/taigiTranslator/model2/translate",
        json={"inputText": text, "inputLan": "Traditional Chinese:zhTW", "outputLan": "Taiwanese:tw"}
    )
    data = resp.json()
    return data.get("outputText") or data.get("result") or text

def generate_v1(text: str, voice_id: str) -> bytes:
    """版本1: 翻譯 → CosyVoice"""
    translated = translate_to_taiwanese(text)
    resp = requests.post(
        f"{BASE_URL}/inference_with_voice_config",
        data={"tts_text": translated, "voice_id": voice_id, "original_text": text}
    )
    resp.raise_for_status()
    return resp.content

def generate_v2(text: str, voice_id: str, seed: int = 2) -> bytes:
    """版本2: IndexTTS 直接生成"""
    resp = requests.post(
        f"{NGINX_URL}/external-tts/tts",
        json={"text": text, "character": voice_id, "seed": seed}
    )
    resp.raise_for_status()
    return resp.content

def generate_both_versions(text: str, voice_id: str, seed: int = 6):
    """並行生成兩個版本"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_v1 = executor.submit(generate_v1, text, voice_id)
        future_v2 = executor.submit(generate_v2, text, voice_id, seed)

        audio_v1 = future_v1.result()
        audio_v2 = future_v2.result()

    with open("output_v1_taiwanese.wav", "wb") as f:
        f.write(audio_v1)
    with open("output_v2_direct.wav", "wb") as f:
        f.write(audio_v2)
    print("兩個版本皆已生成完成！")

# 使用範例
generate_both_versions(
    text="這是一個好日子！你吃飽了嗎？附近有家餐廳好吃喔。",
    voice_id="gentle_female",
    seed=6
)
```

---

## 10. 完整呼叫範例（curl）

### 10.1 取得聲音列表

```bash
curl -X GET http://10.9.0.35:8085/api/voices
```

---

### 10.2 使用聲音配置合成語音

```bash
curl -X POST http://10.9.0.35:8085/api/inference_with_voice_config \
  -F "tts_text=你好，這是一段語音測試" \
  -F "voice_id=gentle_female" \
  -F "original_text=你好，這是一段語音測試" \
  --output output.wav
```

---

### 10.3 使用 IndexTTS 直接合成

```bash
curl -X POST http://10.9.0.35:8085/external-tts/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，這是一段語音測試", "character": "gentle_female", "seed": 6}' \
  --output output_v2.wav
```

---

### 10.4 台語翻譯

```bash
curl -X POST https://learn-language.tokyo/taigiTranslator/model2/translate \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "這是一個好日子！你吃飽了嗎？",
    "inputLan": "Traditional Chinese:zhTW",
    "outputLan": "Taiwanese:tw"
  }'
```

---

### 10.5 零樣本推論（上傳自訂音頻）

```bash
curl -X POST http://10.9.0.35:50001/inference_zero_shot_wav \
  -F "tts_text=你好，歡迎使用 AI 語音系統" \
  -F "prompt_text=這是我的聲音示範" \
  -F "prompt_wav=@/path/to/your_voice.wav" \
  -F "seed=42" \
  --output zero_shot_output.wav
```

---

## 11. 完整呼叫範例（JavaScript / Node.js）

### 11.1 取得聲音列表

```javascript
const response = await fetch('http://10.9.0.35:8085/api/voices');
const data = await response.json();
console.log(data.voices);
```

---

### 11.2 使用聲音配置合成語音（FormData）

```javascript
async function generateAudioV1(text, voiceId) {
  // Step 1: 台語翻譯
  const translateResp = await fetch(
    'https://learn-language.tokyo/taigiTranslator/model2/translate',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        inputText: text,
        inputLan: 'Traditional Chinese:zhTW',
        outputLan: 'Taiwanese:tw'
      })
    }
  );
  const translateData = await translateResp.json();
  const translatedText = translateData.outputText || translateData.result || text;

  // Step 2: CosyVoice TTS
  const formData = new FormData();
  formData.append('tts_text', translatedText);
  formData.append('voice_id', voiceId);
  formData.append('original_text', text);

  const ttsResp = await fetch(
    'http://10.9.0.35:8085/api/inference_with_voice_config',
    { method: 'POST', body: formData }
  );

  const audioBlob = await ttsResp.blob();
  return audioBlob; // 瀏覽器可用 URL.createObjectURL(audioBlob) 播放
}
```

---

### 11.3 使用 IndexTTS 直接合成（JSON）

```javascript
async function generateAudioV2(text, character, seed = 2) {
  const response = await fetch('http://10.9.0.35:8085/external-tts/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, character, seed })
  });

  const audioBlob = await response.blob();
  return audioBlob;
}
```

---

### 11.4 Node.js 儲存音頻（使用 node-fetch）

```javascript
// npm install node-fetch form-data
import fetch from 'node-fetch';
import FormData from 'form-data';
import fs from 'fs';

async function saveTTS(text, voiceId, outputPath) {
  const form = new FormData();
  form.append('tts_text', text);
  form.append('voice_id', voiceId);

  const response = await fetch(
    'http://10.9.0.35:8085/api/inference_with_voice_config',
    { method: 'POST', body: form }
  );

  const buffer = await response.buffer();
  fs.writeFileSync(outputPath, buffer);
  console.log(`已儲存: ${outputPath}`);
}

await saveTTS('你好，測試語音', 'gentle_female', 'output.wav');
```

---

## 12. 錯誤處理

| HTTP 狀態碼 | 原因 | 處理建議 |
|------------|------|---------|
| `404` | `voice_id` 不存在，或聲音配置檔/音頻樣本找不到 | 先呼叫 `GET /voices` 確認可用的 `id` |
| `500` | 聲音合成失敗（模型錯誤、CUDA OOM 等） | 查看伺服器日誌；確認文字長度不超過限制 |
| `422` | 必填欄位缺失 | 確認所有必填參數皆已提供 |
| 翻譯 API 失敗 | 網路問題或外部 API 不可用 | 前端 fallback 使用原始文字繼續生成 |

---

## 13. 注意事項

1. **音頻樣本路徑**：`inference_with_voice_config` 所用的音頻樣本必須存在於伺服器的 `config/audio_samples/` 目錄，路徑由 `voices.local.json` 的 `audio_file` 欄位決定。

2. **文字長度限制**：前端限制 500 字元，後端無硬性限制，但過長文字會增加一次回應時間（CosyVoice 為串流模型，分段越多越久）。

3. **採樣率一致性**：上傳的音頻樣本建議先轉換為 16kHz 單聲道 WAV，伺服器內部使用 `load_wav(file, 16000)` 讀取。

4. **隨機種子（seed）**：相同文字 + 相同種子 = 相同輸出結果，用於複現語音。`voices.local.json` 中的 `seed` 值影響 `inference_with_voice_config` 的輸出穩定性。

5. **CORS**：FastAPI 後端已設定允許所有來源（`*`），直連 `50001` 不會有跨域問題。

6. **IndexTTS 外部服務 IP**：`10.9.0.35:8011` 為內網位址，從外網呼叫需確認網路可達性或透過 Nginx 代理的 `/external-tts/` 路徑訪問。

7. **Docker 部署埠號**：  
   - `PORT` 環境變數控制 FastAPI 直連埠（預設 `50001`）  
   - `WEB_PORT` 控制 Nginx 服務埠（預設 `8085`）

---

*文件生成日期：2026-04-08*  
*對應服務：CosyVoice AI Voice Studio（cosyvoice-service）*
