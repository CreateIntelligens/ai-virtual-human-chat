# 微調模型部署手冊

本手冊旨在指導您如何將使用 `index-tts-lora` 訓練好的微調模型，部署到 `index-tts-vllm` 的運行環境中，替換掉預設的模型。

## 部署流程概述

由於 `index-tts-vllm` 的運行環境需要特定格式的模型檔案，包括 vLLM 格式的 Hugging Face Transformer 模型 (`vllm/` 資料夾) 和原始 PyTorch 權重 (`.pth` 檔案)，因此您需要先將微調後的模型進行轉換和組織。

**核心思想：** 我們將把您微調訓練好的模型相關檔案，組織成類似於原始 `assets/checkpoints/` 資料夾的結構，然後替換掉它。

## 步驟 1: 準備微調模型的中繼資料夾

首先，創建一個臨時資料夾，用於存放和組織您的微調模型相關檔案。

1.  **創建臨時資料夾 (例如：`my_finetuned_model_temp`)：**
    ```bash
    mkdir ./my_finetuned_model_temp
    ```

2.  **複製微調後的 GPT 模型 `.pth` 檔案：**
    將您在 `index-tts-lora` 訓練後生成的 `.pth` 檔案複製到這個臨時資料夾中。
    *   假設您的訓練結果為 `index-tts-lora/checkpoints/gpt_1212_epoch_8.pth`：
        ```bash
        cp ./index-tts-lora/checkpoints/gpt_1212_epoch_8.pth ./my_finetuned_model_temp/gpt_1212_epoch_8.pth
        ```

3.  **複製訓練時使用的 `config.yaml`：**
    將您用於訓練的 `config.yaml` 檔案複製到臨時資料夾，並確保其檔名為 `config.yaml`。
    *   假設為 `index-tts-lora/finetune_models/config.yaml`：
        ```bash
        cp ./index-tts-lora/finetune_models/config.yaml ./my_finetuned_model_temp/config.yaml
        ```

4.  **複製基礎模型資產 (`bpe.model`, `dvae.pth` 和 `bigvgan_generator.pth`)：**
    這些檔案通常來自您原始下載的 IndexTTS-1.5 模型。請從您存放原始模型的路徑複製它們。
    *   假設原始模型資產位於 `assets/checkpoints/`：
        ```bash
        cp ./assets/checkpoints/bpe.model ./my_finetuned_model_temp/bpe.model
        cp ./assets/checkpoints/dvae.pth ./my_finetuned_model_temp/dvae.pth
        cp ./assets/checkpoints/bigvgan_generator.pth ./my_finetuned_model_temp/bigvgan_generator.pth
        ```
        *(如果您不確定它們在哪裡，通常它們與原始的 `gpt.pth` 一同存放於 `assets/checkpoints/` 目錄。)*

5.  **修改 `my_finetuned_model_temp/config.yaml`：**
    打開這個臨時資料夾中的 `config.yaml`，確保以下關鍵配置指向正確的檔案名稱，並包含 `emo_condition_module` 區塊：

    ```yaml
    # 確保 gpt_checkpoint 指向您微調後的 .pth 檔名
    gpt_checkpoint: "gpt_1212_epoch_8.pth" # 應與步驟2複製進來的檔名一致

    # 確保 dvae_checkpoint 和 bigvgan_checkpoint 指向您複製進來的檔名
    dvae_checkpoint: "dvae.pth"
    bigvgan_checkpoint: "bigvgan_generator.pth"

    dataset:
        bpe_model: "bpe.model" # 確保指向您複製進來的 Tokenizer 檔名

    gpt:
        # ... (其他 GPT 配置，保持不變) ...
        condition_module:
            output_size: 512
            linear_units: 2048
            attention_heads: 8
            num_blocks: 6
            input_layer: "conv2d2"
            perceiver_mult: 2
    ```

## 步驟 2: 準備 vLLM 格式的 `vllm/` 資料夾

這一步將會利用 `convert_hf_format.py` 腳本，將您的微調模型轉換為 vLLM 所需的 Hugging Face 格式。轉換腳本會自動創建 `vllm/` 資料夾並生成所需的配置檔案。

1.  **運行 Python 轉換腳本：**
    這個腳本將讀取您臨時資料夾中的 `.pth` 檔案和 `config.yaml`，然後在 `my_finetuned_model_temp/vllm/` 中生成 `model.safetensors`、`config.json`、`generation_config.json`、`tokenizer.json`、`tokenizer_config.json` 等檔案。
    ```bash
    python convert_hf_format.py --model_dir ./my_finetuned_model_temp
    ```
    
    > **注意：** 如果您使用的是 Docker 環境，可以在容器啟動時透過 `entrypoint.sh` 自動執行轉換。設定環境變數 `CONVERT_MODEL=1` 即可。

## 步驟 3: 替換現有的 `assets/checkpoints/` 模型

現在您的 `my_finetuned_model_temp` 資料夾已經包含了所有微調模型運行所需的檔案。接下來，我們將用它來替換掉 `index-tts-vllm` 專案中的 `assets/checkpoints/` 資料夾。

1.  **備份原始的 `assets/checkpoints/` 資料夾 (強烈建議)：**
    在替換之前，請務必備份原始的 `assets/checkpoints/` 資料夾，以防需要還原。
    ```bash
    mv ./assets/checkpoints/ ./assets/checkpoints_backup/
    mkdir -p ./assets/checkpoints/
    ```

2.  **將中繼資料夾的內容複製到 `assets/checkpoints/`：**
    現在，將 `my_finetuned_model_temp` 中的所有內容移動到新的 `assets/checkpoints/` 資料夾。
    *   **將 `gpt_1212_epoch_8.pth` 重新命名為 `gpt.pth` 並移動：**
        ```bash
        mv ./my_finetuned_model_temp/gpt_1212_epoch_8.pth ./assets/checkpoints/gpt.pth
        ```
    *   **將 `config.yaml` 移動：**
        ```bash
        mv ./my_finetuned_model_temp/config.yaml ./assets/checkpoints/config.yaml
        ```
    *   **將 `bpe.model` 移動：**
        ```bash
        mv ./my_finetuned_model_temp/bpe.model ./assets/checkpoints/bpe.model
        ```
    *   **將 `dvae.pth` 移動：**
        ```bash
        mv ./my_finetuned_model_temp/dvae.pth ./assets/checkpoints/dvae.pth
        ```
    *   **將 `bigvgan_generator.pth` 移動：**
        ```bash
        mv ./my_finetuned_model_temp/bigvgan_generator.pth ./assets/checkpoints/bigvgan_generator.pth
        ```
    *   **將完整的 `vllm/` 資料夾移動：**
        ```bash
        mv ./my_finetuned_model_temp/vllm/ ./assets/checkpoints/vllm/
        ```

3.  **清理臨時資料夾：**
    ```bash
    rmdir ./my_finetuned_model_temp
    ```

4.  **驗證檔案結構：**
    確保 `assets/checkpoints/` 目錄包含以下檔案：
    ```
    assets/checkpoints/
    ├── config.yaml
    ├── gpt.pth
    ├── dvae.pth
    ├── bigvgan_generator.pth
    ├── bpe.model
    └── vllm/
        ├── config.json
        ├── generation_config.json
        ├── model.safetensors
        ├── tokenizer.json
        └── tokenizer_config.json
    ```

    **再次檢查：** 確保 `assets/checkpoints/config.yaml` 中的 `gpt_checkpoint` 配置現在指向 `"gpt.pth"`。如果您之前已經修改為 `gpt_1212_epoch_8.pth`，現在需要手動將其改回 `gpt.pth`，因為您已經將檔案重新命名。

## 步驟 4: 啟動服務

現在，您的 `assets/checkpoints/` 資料夾已經包含了您微調後的模型。您可以按照正常方式啟動 `index-tts-vllm` 服務。

### 方式 1: 直接運行 Python 腳本

```bash
python api_server.py --model_dir ./assets/checkpoints --port 8001
```

### 方式 2: 使用 Docker Compose

如果您使用 Docker Compose，請確保您的 `docker-compose.yaml` 正確掛載了 `assets/checkpoints/` 目錄：

```bash
docker compose up
```

預設情況下，`docker-compose.yaml` 已經將整個專案目錄掛載到容器中，因此無需額外配置。

### 驗證服務

服務啟動後，您可以透過以下方式驗證：

```bash
# 檢查健康狀態
curl http://localhost:8001/health

# 測試 TTS API
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "測試微調模型", "character": "test"}' \
  --output test.wav
```

透過這些步驟，您的微調模型應該就能在 `index-tts-vllm` 環境中正常運行了。

## 常見問題

**Q: 轉換過程中出現錯誤怎麼辦？**

A: 請檢查 `config.yaml` 中的配置是否正確，特別是 `gpt_checkpoint` 路徑。確保所有必需的檔案都已複製到臨時資料夾中。

**Q: 如何確認模型是否正確載入？**

A: 查看服務啟動日誌，確認看到類似 "GPT weights restored from: ..." 的訊息。也可以檢查 `logs/` 目錄中的日誌檔案。

**Q: 需要重新訓練 DVAE 或 BigVGAN 嗎？**

A: 通常不需要。DVAE 和 BigVGAN 是通用的聲學模型組件，可以直接使用原始模型的檔案。只有 GPT 部分需要微調。
