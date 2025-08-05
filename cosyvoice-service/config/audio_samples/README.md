# 語音樣本目錄

此目錄用於存放語音樣本檔案，這些檔案將被 AI 模型用於學習聲音特徵。

## 📁 檔案要求

### 音頻格式
- **支援格式**: WAV, MP3, FLAC
- **推薦格式**: WAV (16-bit, 22.05kHz 或更高)
- **聲道**: 單聲道或立體聲
- **檔案大小**: 建議小於 10MB

### 音頻品質
- **時長**: 建議 3-10 秒
- **內容**: 清晰的語音，避免背景噪音
- **語速**: 正常語速，發音清晰
- **音量**: 適中音量，避免過大或過小

## 📝 檔案命名

建議使用描述性的檔案名稱，例如：
- `gentle_female.wav` - 溫柔女聲
- `professional_male.wav` - 專業男聲
- `cheerful_female.wav` - 活潑女聲

## ⚙️ 配置檔案系統

### 檔案說明
- `config/voices.example.json` - 範例配置檔案（提交到 Git）
- `config/voices.local.json` - 您的個人配置（Git 忽略）

### 首次設定
如果您是第一次配置，需要先建立個人配置檔案：
```bash
# 複製範例配置作為起始點
cp config/voices.example.json config/voices.local.json
```

### 配置檔案自動選擇
系統會自動選擇配置檔案：
- ✅ 優先使用 `voices.local.json`（個人配置）
- ✅ 如果不存在，則使用 `voices.example.json`（範例配置）
- ✅ 啟動時會在日誌中顯示使用的配置檔案

### 隱私保護
- 🔒 `voices.local.json` 不會被提交到 Git
- 🔒 您的個人聲音配置保持私密
- 🔒 其他開發者有清晰的範例可參考

## 📝 配置步驟

1. **添加音頻檔案**
   ```bash
   # 將語音樣本複製到此目錄
   cp your_voice_sample.wav config/audio_samples/
   ```

2. **更新配置檔案**
   編輯 `config/voices.local.json`（如果不存在，請先複製範例配置）：
   ```bash
   # 首次設定時複製範例配置
   cp config/voices.example.json config/voices.local.json
   ```
   
   然後編輯 `voices.local.json` 添加新的聲音配置：
   ```json
   {
     "id": "your_voice_id",
     "name": "您的聲音名稱",
     "prompt_text": "與音頻內容對應的文字",
     "audio_file": "your_voice_sample.wav",
     "seed": 12345,
     "description": "聲音描述"
   }
   ```

3. **重啟服務**
   ```bash
   docker-compose restart ai-voice-studio
   ```

## 🎯 最佳實踐

### 錄音建議
- 使用高品質麥克風
- 在安靜環境中錄音
- 保持一致的音量和語速
- 避免口音過重或發音不清

### 文字內容
- 選擇自然、流暢的句子
- 避免過於技術性的詞彙
- 包含常見的語音變化（升調、降調）

### 範例內容
```
"你好，歡迎使用我們的語音服務，希望能為您提供優質的體驗。"
"這是一個專業的語音示範，適合商務和正式場合使用。"
"大家好，很高興為您服務，讓我們一起探索 AI 語音的魅力吧！"
```

## 🔒 安全注意事項

- 確保您有權使用所上傳的語音樣本
- 不要上傳包含敏感資訊的音頻
- 定期備份重要的語音樣本檔案
- 注意檔案大小，避免佔用過多存儲空間

## 📞 技術支援

如果您在配置語音樣本時遇到問題，請參考主要的 README.md 檔案或聯繫技術支援。
