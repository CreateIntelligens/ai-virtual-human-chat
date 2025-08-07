from fastapi import FastAPI, File, UploadFile, HTTPException, Form  # 添加Form導入
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
import time
import argparse
import subprocess
import sys
from indextts.infer import IndexTTS

def check_and_download_models(model_dir):
    """檢查模型文件是否存在，如果不存在則下載"""
    required_files = [
        "bigvgan_generator.pth",
        "bpe.model", 
        "gpt.pth",
        "config.yaml",
        "bigvgan_discriminator.pth",
        "dvae.pth",
        "unigram_12000.vocab"
    ]
    
    # 檢查所有必要文件是否存在
    missing_files = []
    for file in required_files:
        file_path = os.path.join(model_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ 所有模型文件已存在，跳過下載")
        return True
    
    print(f"📥 檢測到 {len(missing_files)} 個缺失的模型文件，開始下載...")
    print(f"缺失文件: {', '.join(missing_files)}")
    
    # 確保模型目錄存在
    os.makedirs(model_dir, exist_ok=True)
    
    try:
        # 使用 huggingface-cli 下載模型 - 修正語法
        download_cmd = [
            "huggingface-cli", "download", "IndexTeam/IndexTTS-1.5",
            "--local-dir", model_dir,
            "--local-dir-use-symlinks", "False"
        ]
        
        print("🔄 使用 huggingface-cli 下載模型...")
        print(f"📝 執行命令: {' '.join(download_cmd)}")
        
        result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=1800)  # 30分鐘超時
        
        if result.returncode == 0:
            print("✅ 模型下載完成")
            print(f"📤 下載輸出: {result.stdout}")
            
            # 驗證文件是否都已下載
            still_missing = []
            for file in required_files:
                file_path = os.path.join(model_dir, file)
                if not os.path.exists(file_path):
                    still_missing.append(file)
            
            if still_missing:
                print(f"❌ 仍有文件缺失: {', '.join(still_missing)}")
                return False
            
            print("🎉 所有模型文件驗證完成")
            return True
        else:
            print(f"❌ huggingface-cli 下載失敗: {result.stderr}")
            print(f"📤 標準輸出: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 模型下載超時")
        return False
    except Exception as e:
        print(f"❌ 模型下載過程中發生錯誤: {e}")
        return False

# 新增獨立配置
parser = argparse.ArgumentParser(description="IndexTTS API")
parser.add_argument("--port", type=int, default=6008, help="API服務端口")
parser.add_argument("--host", type=str, default="0.0.0.0", help="API服務地址")
parser.add_argument("--model_dir", type=str, default="checkpoints", help="模型目錄")
api_args = parser.parse_args()

# 檢查並下載模型（如果需要）
print("🔍 檢查 IndexTTS 模型文件...")
if not check_and_download_models(api_args.model_dir):
    print("❌ 模型文件檢查或下載失敗，無法啟動服務")
    sys.exit(1)

# 初始化模型
print("🚀 初始化 IndexTTS 模型...")
try:
    tts = IndexTTS(
        model_dir=api_args.model_dir,
        cfg_path=os.path.join(api_args.model_dir, "config.yaml")
    )
    print("✅ IndexTTS 模型初始化完成")
except Exception as e:
    print(f"❌ IndexTTS 模型初始化失敗: {e}")
    sys.exit(1)

COUNT = 0

app = FastAPI(title="IndexTTS API")

class TTSRequest(BaseModel):
    text: str
    infer_mode: str = "普通推理"
    max_text_tokens_per_sentence: int = 120
    sentences_bucket_max_size: int = 4
    do_sample: bool = True
    top_p: float = 0.8
    top_k: int = 30
    temperature: float = 1.0
    length_penalty: float = 0.0
    num_beams: int = 3
    repetition_penalty: float = 10.0
    max_mel_tokens: int = 600

@app.post("/tts")
async def synthesize(
    prompt_audio: UploadFile = File(..., description="參考音頻檔案"),
    text: str = Form(..., examples=["歡迎使用語音合成介面"]),
    infer_mode: str = Form("普通推理"),
    max_text_tokens_per_sentence: int = Form(120),
    sentences_bucket_max_size: int = Form(4),
    do_sample: bool = Form(True),
    top_p: float = Form(0.8),
    top_k: int = Form(30),
    temperature: float = Form(1.0),
    length_penalty: float = Form(0.0),
    num_beams: int = Form(3),
    repetition_penalty: float = Form(10.0),
    max_mel_tokens: int = Form(600)
):
    """單次推理介面"""
    try:
        global COUNT

        # 創建輸出目錄
        os.makedirs("outputs", exist_ok=True)
        
        # 保存上傳的參考音頻
        prompt_path = f"temp_prompt_{int(time.time())}.wav"
        with open(prompt_path, "wb") as f:
            f.write(await prompt_audio.read())
        
        # 準備輸出路徑 循環1000次覆蓋
        COUNT += 1
        if COUNT > 1000:
            COUNT = 0
        output_path = os.path.join("outputs", f"api_output_{COUNT}.wav")

        
        # 調用生成邏輯
        kwargs = {
            "do_sample": do_sample,
            "top_p": top_p,
            "top_k": top_k if top_k > 0 else None,
            "temperature": temperature,
            "length_penalty": length_penalty,
            "num_beams": num_beams,
            "repetition_penalty": repetition_penalty,
            "max_mel_tokens": max_mel_tokens,
        }

        if infer_mode == "普通推理":
            tts.infer(
                prompt_path,
                text,
                output_path,
                max_text_tokens_per_sentence=max_text_tokens_per_sentence,
                **kwargs
            )
        else:
            tts.infer_fast(
                prompt_path,
                text,
                output_path,
                max_text_tokens_per_sentence=max_text_tokens_per_sentence,
                sentences_bucket_max_size=sentences_bucket_max_size,
                **kwargs
            )
        
        os.remove(prompt_path)
        return FileResponse(output_path, media_type="audio/wav")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=api_args.host, port=api_args.port)
