#!/bin/bash

###############################################################################
# 微調模型部署腳本
# 此腳本用於自動化部署 index-tts-lora 訓練好的微調模型到 index-tts-vllm 環境
###############################################################################

set -e  # 遇到錯誤立即退出

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 輸出函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查必要參數
usage() {
    cat << EOF
使用方法: $0 [選項]

選項:
    -m, --model-path PATH       必填：微調後的 .pth 模型檔案路徑
    -c, --config-path PATH      必填：訓練時使用的 config.yaml 檔案路徑
    -l, --lora-dir PATH         選填：index-tts-lora 專案目錄（用於自動尋找模型和配置）
    -t, --temp-dir PATH         選填：臨時資料夾名稱（預設：my_finetuned_model_temp）
    -b, --backup                選填：是否備份原始 checkpoints（預設：是）
    --no-backup                 選填：不備份原始 checkpoints
    -h, --help                  顯示此幫助訊息

範例:
    # 方式1: 指定模型和配置檔案路徑
    $0 -m ./index-tts-lora/checkpoints/gpt_1212_epoch_8.pth -c ./index-tts-lora/finetune_models/config.yaml

    # 方式2: 指定 lora 專案目錄（會自動尋找最新的模型）
    $0 -l ./index-tts-lora

EOF
}

# 預設參數
MODEL_PATH=""
CONFIG_PATH=""
LORA_DIR=""
TEMP_DIR="my_finetuned_model_temp"
BACKUP=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKPOINT_DIR="${SCRIPT_DIR}/assets/checkpoints"

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model-path)
            MODEL_PATH="$2"
            shift 2
            ;;
        -c|--config-path)
            CONFIG_PATH="$2"
            shift 2
            ;;
        -l|--lora-dir)
            LORA_DIR="$2"
            shift 2
            ;;
        -t|--temp-dir)
            TEMP_DIR="$2"
            shift 2
            ;;
        -b|--backup)
            BACKUP=true
            shift
            ;;
        --no-backup)
            BACKUP=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "未知參數: $1"
            usage
            exit 1
            ;;
    esac
done

# 如果指定了 LORA_DIR，自動尋找模型和配置
if [[ -n "$LORA_DIR" ]]; then
    log_info "從 LORA 目錄自動尋找模型和配置: $LORA_DIR"
    
    # 尋找最新的 .pth 檔案
    if [[ -z "$MODEL_PATH" ]]; then
        MODEL_PATH=$(find "$LORA_DIR/checkpoints" -name "*.pth" -type f 2>/dev/null | sort -r | head -n 1)
        if [[ -z "$MODEL_PATH" ]]; then
            log_error "無法在 $LORA_DIR/checkpoints 找到 .pth 模型檔案"
            exit 1
        fi
        log_info "找到模型檔案: $MODEL_PATH"
    fi
    
    # 尋找 config.yaml
    if [[ -z "$CONFIG_PATH" ]]; then
        if [[ -f "$LORA_DIR/finetune_models/config.yaml" ]]; then
            CONFIG_PATH="$LORA_DIR/finetune_models/config.yaml"
        elif [[ -f "$LORA_DIR/config.yaml" ]]; then
            CONFIG_PATH="$LORA_DIR/config.yaml"
        else
            log_error "無法在 $LORA_DIR 找到 config.yaml"
            exit 1
        fi
        log_info "找到配置檔案: $CONFIG_PATH"
    fi
fi

# 驗證必要參數
if [[ -z "$MODEL_PATH" ]] || [[ -z "$CONFIG_PATH" ]]; then
    log_error "缺少必要參數"
    usage
    exit 1
fi

# 驗證檔案存在
if [[ ! -f "$MODEL_PATH" ]]; then
    log_error "模型檔案不存在: $MODEL_PATH"
    exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
    log_error "配置檔案不存在: $CONFIG_PATH"
    exit 1
fi

# 取得模型檔案名稱
MODEL_FILENAME=$(basename "$MODEL_PATH")
log_info "開始部署微調模型: $MODEL_FILENAME"

###############################################################################
# 步驟 1: 準備微調模型的中繼資料夾
###############################################################################
log_info "步驟 1/4: 準備中繼資料夾 $TEMP_DIR"

# 清理並創建臨時資料夾
if [[ -d "$TEMP_DIR" ]]; then
    log_warn "臨時資料夾已存在，將清空它"
    rm -rf "$TEMP_DIR"
fi
mkdir -p "$TEMP_DIR"

# 複製微調後的 GPT 模型
log_info "複製微調後的 GPT 模型..."
cp "$MODEL_PATH" "$TEMP_DIR/$MODEL_FILENAME"

# 複製訓練時使用的 config.yaml
log_info "複製配置檔案..."
cp "$CONFIG_PATH" "$TEMP_DIR/config.yaml"

# 複製基礎模型資產
log_info "複製基礎模型資產..."
if [[ ! -d "$CHECKPOINT_DIR" ]]; then
    log_error "找不到原始 checkpoints 目錄: $CHECKPOINT_DIR"
    exit 1
fi

for file in bpe.model dvae.pth bigvgan_generator.pth; do
    if [[ -f "$CHECKPOINT_DIR/$file" ]]; then
        cp "$CHECKPOINT_DIR/$file" "$TEMP_DIR/$file"
        log_info "  ✓ 已複製 $file"
    else
        log_error "找不到必要檔案: $CHECKPOINT_DIR/$file"
        exit 1
    fi
done

# 修改 config.yaml 中的 gpt_checkpoint 路徑
log_info "更新配置檔案中的模型路徑..."
sed -i "s|gpt_checkpoint:.*|gpt_checkpoint: \"$MODEL_FILENAME\"|g" "$TEMP_DIR/config.yaml"

###############################################################################
# 步驟 2: 準備 vLLM 格式的 vllm/ 資料夾
###############################################################################
log_info "步驟 2/4: 轉換模型為 vLLM 格式"

if [[ ! -f "${SCRIPT_DIR}/convert_hf_format.py" ]]; then
    log_error "找不到轉換腳本: convert_hf_format.py"
    exit 1
fi

cd "$SCRIPT_DIR"
log_info "執行模型格式轉換..."
python convert_hf_format.py --model_dir "./$TEMP_DIR"

# 驗證 vllm 資料夾是否生成
if [[ ! -d "$TEMP_DIR/vllm" ]]; then
    log_error "vLLM 格式轉換失敗，未生成 vllm/ 資料夾"
    exit 1
fi
log_info "  ✓ vLLM 格式轉換完成"

###############################################################################
# 步驟 3: 替換現有的 assets/checkpoints/ 模型
###############################################################################
log_info "步驟 3/4: 替換 assets/checkpoints/ 模型"

# 備份原始的 checkpoints
if [[ "$BACKUP" == true ]]; then
    BACKUP_DIR="${CHECKPOINT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    log_info "備份原始 checkpoints 到: $BACKUP_DIR"
    mv "$CHECKPOINT_DIR" "$BACKUP_DIR"
    mkdir -p "$CHECKPOINT_DIR"
fi

# 將 gpt 模型重新命名為 gpt.pth 並移動
log_info "部署模型檔案..."
mv "$TEMP_DIR/$MODEL_FILENAME" "$CHECKPOINT_DIR/gpt.pth"

# 移動其他檔案
mv "$TEMP_DIR/config.yaml" "$CHECKPOINT_DIR/config.yaml"
mv "$TEMP_DIR/bpe.model" "$CHECKPOINT_DIR/bpe.model"
mv "$TEMP_DIR/dvae.pth" "$CHECKPOINT_DIR/dvae.pth"
mv "$TEMP_DIR/bigvgan_generator.pth" "$CHECKPOINT_DIR/bigvgan_generator.pth"
mv "$TEMP_DIR/vllm" "$CHECKPOINT_DIR/vllm"

# 更新 config.yaml 中的 gpt_checkpoint 為 gpt.pth
sed -i 's|gpt_checkpoint:.*|gpt_checkpoint: "gpt.pth"|g' "$CHECKPOINT_DIR/config.yaml"

# 清理臨時資料夾
log_info "清理臨時資料夾..."
rmdir "$TEMP_DIR"

###############################################################################
# 步驟 4: 驗證檔案結構
###############################################################################
log_info "步驟 4/4: 驗證部署結果"

REQUIRED_FILES=(
    "config.yaml"
    "gpt.pth"
    "dvae.pth"
    "bigvgan_generator.pth"
    "bpe.model"
    "vllm/config.json"
    "vllm/generation_config.json"
    "vllm/model.safetensors"
    "vllm/tokenizer.json"
    "vllm/tokenizer_config.json"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$CHECKPOINT_DIR/$file" ]]; then
        log_info "  ✓ $file"
    else
        log_error "  ✗ $file 不存在"
        ALL_EXIST=false
    fi
done

if [[ "$ALL_EXIST" == false ]]; then
    log_error "部分檔案缺失，部署可能不完整"
    exit 1
fi

###############################################################################
# 完成
###############################################################################
log_info "================================================"
log_info "✓ 微調模型部署完成！"
log_info "================================================"
log_info ""
log_info "您現在可以啟動服務："
log_info ""
log_info "  方式 1 - 直接運行："
log_info "    python api_server.py --model_dir ./assets/checkpoints --port 8001"
log_info ""
log_info "  方式 2 - 使用 Docker Compose："
log_info "    docker compose up"
log_info ""
log_info "驗證服務："
log_info "    curl http://localhost:8001/health"
log_info ""

if [[ "$BACKUP" == true ]]; then
    log_info "原始模型已備份至: $BACKUP_DIR"
    log_info "如需還原，執行: mv $BACKUP_DIR $CHECKPOINT_DIR"
fi
