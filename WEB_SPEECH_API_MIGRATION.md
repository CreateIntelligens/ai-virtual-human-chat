# Web Speech API 遷移說明

## 概述

本專案已將語音識別功能從 **SenseVoice STT 服務** 遷移至 **瀏覽器原生的 Web Speech API**，以節省 GPU 顯存並簡化部署架構。

## 主要變更

### 1. 前端變更

#### 新測試文件
- **文件位置**: `/web_demo/static/chat_room_no_watermark_test.html`
- **說明**: 這是使用 Web Speech API 的測試版本

#### 核心改動
- ❌ 移除了 MediaRecorder 音頻錄製
- ❌ 移除了 VAD (Voice Activity Detection) 功能
- ❌ 移除了與 SenseVoice STT API 的通信
- ✅ 新增了 Web Speech API 語音識別
- ✅ 保持了相同的 UI 和用戶體驗

### 2. 後端變更

#### Docker Compose
- **文件**: `docker-compose.yaml`
- **變更**: 註釋掉了 `sensevoice-service` 服務
- **影響**: 主服務 `ai-virtual-human` 不再依賴 SenseVoice 服務

#### 節省資源
- 🚀 不再需要運行 SenseVoice GPU 服務
- 💾 節省顯存佔用
- ⚡ 減少容器啟動時間

## 功能對比

| 功能 | SenseVoice STT | Web Speech API |
|-----|---------------|----------------|
| **部署複雜度** | 需要獨立服務 + GPU | 無需額外服務 |
| **GPU 使用** | 需要 | 不需要 |
| **語言支持** | 多語言（中文優化） | 多語言（依賴 Google） |
| **離線使用** | 可以（本地模型） | 不可以（需要網絡） |
| **準確度** | 高（中文優化） | 高（Google 服務） |
| **延遲** | 低（本地處理） | 中等（網絡請求） |
| **瀏覽器支持** | 全部（透過後端） | Chrome/Edge |
| **成本** | GPU 資源 | 免費（有限制） |

## 使用方式

### 測試新版本

1. **啟動服務**（不含 SenseVoice）
   ```bash
   docker-compose up -d
   ```

2. **訪問測試頁面**
   ```
   http://localhost:8888/static/chat_room_no_watermark_test.html
   ```

3. **使用語音功能**
   - 點擊麥克風按鈕開始說話
   - 瀏覽器會請求麥克風權限（首次使用）
   - 說完後自動停止識別或手動點擊停止
   - 識別結果會自動進入對話流程

### 瀏覽器要求

**推薦瀏覽器**:
- ✅ Google Chrome (推薦)
- ✅ Microsoft Edge
- ✅ Opera

**不支持**:
- ❌ Firefox (需要特殊配置)
- ❌ Safari (部分支持)

### 網絡要求

- ⚠️ **需要網絡連接**: Web Speech API 使用 Google 的語音識別服務
- ⚠️ **HTTPS 或 localhost**: Web Speech API 只在安全上下文中工作

## 配置參數

在 `chat_room_no_watermark_test.html` 中可以調整以下參數：

```javascript
const RECOGNITION_CONFIG = {
    LANG: 'zh-TW',              // 語言設定（繁體中文）
    CONTINUOUS: false,          // 不連續識別（說完一句就停止）
    INTERIM_RESULTS: true,      // 顯示臨時結果
    MAX_ALTERNATIVES: 1,        // 最多返回1個結果
    MAX_SILENCE_TIME: 3000      // 最大靜音時間（毫秒）
};
```

### 支持的語言代碼

| 語言 | 代碼 |
|-----|------|
| 繁體中文 | `zh-TW` |
| 簡體中文 | `zh-CN` |
| 英文（美國） | `en-US` |
| 英文（英國） | `en-GB` |
| 日文 | `ja-JP` |
| 韓文 | `ko-KR` |

## 故障排除

### 問題 1: 瀏覽器不支持語音識別

**症狀**: 頁面顯示"您的瀏覽器不支持語音識別"

**解決方案**:
1. 使用 Chrome 或 Edge 瀏覽器
2. 確保瀏覽器版本最新

### 問題 2: 無法訪問麥克風

**症狀**: 點擊麥克風按鈕後沒有反應

**解決方案**:
1. 檢查瀏覽器麥克風權限設置
2. 確保沒有其他應用佔用麥克風
3. 使用 HTTPS 或 localhost 訪問

### 問題 3: 網絡錯誤

**症狀**: 顯示"網絡錯誤，請檢查網絡連接"

**解決方案**:
1. 檢查網絡連接
2. 確認可以訪問 Google 服務
3. 檢查防火牆設置

### 問題 4: 識別不準確

**症狀**: 語音識別結果不正確

**解決方案**:
1. 確保環境安靜
2. 清晰地說話
3. 調整 `LANG` 參數匹配您的語言
4. 靠近麥克風說話

## 性能優化

### 1. 減少 GPU 使用

修改 `docker-compose.yaml` 中的 GPU 配置：

```yaml
# IndexTTS 服務
environment:
  - GPU_MEMORY_UTILIZATION=0.1  # 降低 GPU 記憶體使用率
```

### 2. 使用 CPU 模式（可選）

如果不需要 TTS 功能的極致性能，可以考慮使用 EdgeTTS（不需要 GPU）：

```javascript
// 在前端選擇 EdgeTTS 聲音
voiceDropdown.value = 'female-tianmei';  // EdgeTTS 甜美女聲
```

## 回滾到 SenseVoice（如果需要）

如果需要回到 SenseVoice STT 服務：

1. **取消註釋 docker-compose.yaml**
   ```yaml
   sensevoice-service:  # 移除註釋符號
     build: ./sensevoice-service
     # ... 其他配置
   ```

2. **恢復依賴**
   ```yaml
   depends_on:
     sensevoice-service:
       condition: service_healthy
   ```

3. **使用原始頁面**
   ```
   http://localhost:8888/static/chat_room_no_watermark.html
   ```

## 未來計劃

- [ ] 添加語音識別設置面板（語言、方言選擇）
- [ ] 支持多種識別引擎切換
- [ ] 添加離線語音識別選項
- [ ] 優化識別準確度

## 技術支持

如有問題，請查看：
- 瀏覽器控制台日誌（F12 開發者工具）
- Docker 容器日誌：`docker-compose logs -f`
- GitHub Issues

---

**更新日期**: 2026-04-01
**版本**: 1.0.0
