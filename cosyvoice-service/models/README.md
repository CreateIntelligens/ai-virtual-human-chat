# CosyVoice 模型目錄

## 📁 目錄說明

此目錄用於存放您的 CosyVoice 微調模型文件。

## 🎯 模型放置方式

請將您的微調模型按以下結構放置：

```
cosyvoice_models/
└── trained_models20250801/
    └── cosyvoice2/
        ├── model.pt
        ├── config.yaml
        └── 其他模型文件...
```

## ⚙️ 配置說明

1. **模型路徑配置**：在 `.env` 文件中設置：
   ```bash
   COSYVOICE_MODEL_PATH=./cosyvoice_models/trained_models20250801
   ```

2. **Docker 掛載**：`docker-compose.yaml` 會自動掛載此目錄到容器中

## 📝 注意事項

- ⚠️ 模型文件通常很大，已被 `.gitignore` 忽略，不會進入版本控制
- ✅ 目錄結構會被保留，方便其他用戶了解如何放置模型
- 🔄 如果您的模型目錄結構不同，請相應調整 `.env` 中的路徑配置

## 🚀 使用方法

1. 將您的微調模型放置在此目錄下
2. 確保 `.env` 文件中的路徑配置正確
3. 啟動 Docker 服務：`docker-compose up --build`
4. CosyVoice 服務會自動載入您的模型

## 🔧 故障排除

如果模型載入失敗，請檢查：
- 模型文件是否完整
- 路徑配置是否正確
- Docker 容器是否有足夠的記憶體
- 查看容器日誌：`docker-compose logs cosyvoice-service`
