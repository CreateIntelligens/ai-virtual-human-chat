
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "7"

import asyncio
import io
import traceback
import tempfile
import uuid
import subprocess
from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import argparse
import json
import asyncio
import time
import numpy as np
import soundfile as sf

from indextts.infer_vllm import IndexTTS

# 嘗試導入 OpenCC 進行繁簡轉換
try:
    from opencc import OpenCC
    opencc_t2s = OpenCC('t2s')  # 繁體轉簡體
    OPENCC_AVAILABLE = True
    print("OpenCC 繁簡轉換功能已啟用")
except ImportError:
    OPENCC_AVAILABLE = False
    opencc_t2s = None
    print("OpenCC 未安裝，繁簡轉換功能將被停用")

# 全域詞庫變數
custom_dict = {}

def load_custom_dict():
    """載入自定義詞庫"""
    global custom_dict
    try:
        current_file_path = os.path.abspath(__file__)
        cur_dir = os.path.dirname(current_file_path)
        dict_path = os.path.join(cur_dir, "custom_dict.json")
        
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                custom_dict = json.load(f)
            print(f"成功載入詞庫，共 {len(custom_dict)} 個詞條")
        else:
            print(f"詞庫檔案不存在: {dict_path}")
            custom_dict = {}
    except Exception as e:
        print(f"載入詞庫時發生錯誤: {e}")
        custom_dict = {}

def get_speaker_default_seed(speaker_name, fallback_seed=8):
    """獲取 speaker 的預設 seed 值"""
    try:
        current_file_path = os.path.abspath(__file__)
        cur_dir = os.path.dirname(current_file_path)
        speaker_path = os.path.join(cur_dir, "assets/speaker.json")
        
        if os.path.exists(speaker_path):
            with open(speaker_path, 'r', encoding='utf-8') as f:
                speaker_dict = json.load(f)
            
            speaker_config = speaker_dict.get(speaker_name)
            if speaker_config and isinstance(speaker_config, dict):
                return speaker_config.get("default_seed", fallback_seed)
        
        return fallback_seed
    except Exception as e:
        print(f"獲取 speaker 預設 seed 時發生錯誤: {e}")
        return fallback_seed

def traditional_to_simplified(text):
    """將繁體字轉換為簡體字"""
    if not OPENCC_AVAILABLE or not opencc_t2s:
        return text
    
    try:
        simplified_text = opencc_t2s.convert(text)
        if simplified_text != text:
            print(f"繁簡轉換: '{text}' -> '{simplified_text}'")
        return simplified_text
    except Exception as e:
        print(f"繁簡轉換時發生錯誤: {e}")
        return text

def apply_custom_dict(text):
    """將文字根據自定義詞庫進行轉換"""
    if not custom_dict:
        return text
    
    converted_text = text
    for original, replacement in custom_dict.items():
        converted_text = converted_text.replace(original, replacement)
    
    if converted_text != text:
        print(f"詞庫轉換: '{text}' -> '{converted_text}'")
    
    return converted_text

def process_text_for_tts(text):
    """完整的文字處理流程：自定義詞庫轉換 -> 繁簡轉換"""
    # 步驟 1: 應用自定義詞庫轉換
    dict_converted_text = apply_custom_dict(text)
    
    # 步驟 2: 繁體轉簡體
    final_text = traditional_to_simplified(dict_converted_text)
    
    # 如果有任何轉換，顯示完整的轉換過程
    if final_text != text:
        print(f"完整文字處理: '{text}' -> '{final_text}'")
    
    return final_text

def convert_audio_with_ffmpeg(input_data, text="", input_format='wav', output_format='wav', target_sample_rate=16000):
    """
    使用ffmpeg轉換音檔格式和採樣率，確保20ms幀長度
    對於16kHz採樣率，20ms = 320 samples
    """
    try:
        # 建立臨時檔案
        with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as temp_input:
            temp_input.write(input_data)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        # 計算20ms的幀大小 (samples)
        frame_size_samples = int(target_sample_rate * 0.02)  # 20ms in samples
        
        # 使用ffmpeg轉換，確保音檔符合20ms幀長度要求
        cmd = [
            'ffmpeg', '-y',  # -y 覆蓋輸出檔案
            '-i', temp_input_path,  # 輸入檔案
            '-ar', str(target_sample_rate),  # 設定採樣率 16000Hz
            '-ac', '1',  # 單聲道
            '-c:a', 'pcm_s16le',  # 16-bit PCM 格式
            '-f', 'wav',  # 明確指定WAV格式
            temp_output_path  # 輸出檔案
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        # 讀取轉換後的檔案
        with open(temp_output_path, 'rb') as f:
            output_data = f.read()
        
        # 驗證轉換結果 (可選，用於debug)
        print(f"文字內容: {text}")
        print(f"已轉換音檔: 採樣率={target_sample_rate}Hz, 20ms幀={frame_size_samples}樣本")
        
        # 清理臨時檔案
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        
        return output_data
    
    except Exception as e:
        # 清理臨時檔案（如果存在）
        for path in [temp_input_path, temp_output_path]:
            if 'path' in locals() and os.path.exists(path):
                os.unlink(path)
        raise e

tts = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts
    cfg_path = os.path.join(args.model_dir, "config.yaml")
    tts = IndexTTS(model_dir=args.model_dir, cfg_path=cfg_path, gpu_memory_utilization=args.gpu_memory_utilization)

    # 載入自定義詞庫
    load_custom_dict()

    current_file_path = os.path.abspath(__file__)
    cur_dir = os.path.dirname(current_file_path)
    speaker_path = os.path.join(cur_dir, "assets/speaker.json")
    if os.path.exists(speaker_path):
        speaker_dict = json.load(open(speaker_path, 'r'))

        for speaker, speaker_config in speaker_dict.items():
            # 支援舊格式（直接是音頻路徑列表）和新格式（包含配置的字典）
            if isinstance(speaker_config, list):
                # 舊格式：直接是音頻路徑列表
                audio_paths = speaker_config
            else:
                # 新格式：包含 audio_paths 和其他配置
                audio_paths = speaker_config.get("audio_paths", [])
            
            audio_paths_ = []
            for audio_path in audio_paths:
                audio_paths_.append(os.path.join(cur_dir, audio_path))
            tts.registry_speaker(speaker, audio_paths_)
    yield
    # Clean up the ML models and release the resources
    # ml_models.clear()

app = FastAPI(lifespan=lifespan)

# 添加CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        global tts
        if tts is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "TTS model not initialized"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "message": "Service is running",
                "timestamp": time.time()
            }
        )
    except Exception as ex:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(ex)
            }
        )


@app.post("/tts_url", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api_url(request: Request):
    try:
        data = await request.json()
        text = data["text"]
        audio_paths = data["audio_paths"]
        seed = data.get("seed", 8)

        # 完整文字處理：詞庫轉換 + 繁簡轉換
        processed_text = process_text_for_tts(text)

        global tts
        sr, wav = await tts.infer(audio_paths, processed_text, seed=seed)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=processed_text, target_sample_rate=16000)
        return Response(content=wav_bytes_16k, media_type="audio/wav")
    
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )


@app.post("/tts", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api(request: Request):
    try:
        data = await request.json()
        text = data["text"]
        character = data["character"]
        
        # 優先使用 API 請求中的 seed，否則使用 speaker 的預設 seed
        if "seed" in data:
            seed = data["seed"]
        else:
            seed = get_speaker_default_seed(character, fallback_seed=8)

        # 完整文字處理：詞庫轉換 + 繁簡轉換
        processed_text = process_text_for_tts(text)

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, processed_text, seed=seed)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=processed_text, target_sample_rate=16000)
        return Response(content=wav_bytes_16k, media_type="audio/wav")
    
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        print(tb_str)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )



@app.get("/audio/voices")
async def tts_voices():
    """ additional function to provide the list of available voices, in the form of JSON """
    current_file_path = os.path.abspath(__file__)
    cur_dir = os.path.dirname(current_file_path)
    speaker_path = os.path.join(cur_dir, "assets/speaker.json")
    if os.path.exists(speaker_path):
        speaker_dict = json.load(open(speaker_path, 'r'))
        return speaker_dict
    else:
        return []


@app.post("/reload_dict")
async def reload_custom_dict():
    """重新載入自定義詞庫"""
    try:
        load_custom_dict()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"詞庫重新載入成功，共 {len(custom_dict)} 個詞條",
                "dict_count": len(custom_dict)
            }
        )
    except Exception as ex:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(ex)
            }
        )


@app.get("/dict_status")
async def get_dict_status():
    """獲取當前詞庫狀態"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "dict_count": len(custom_dict),
            "dictionary": custom_dict
        }
    )


@app.post("/test_text_processing")
async def test_text_processing(request: Request):
    """測試文字處理功能（詞庫轉換 + 繁簡轉換）"""
    try:
        data = await request.json()
        original_text = data["text"]
        
        # 步驟 1: 詞庫轉換
        dict_converted = apply_custom_dict(original_text)
        
        # 步驟 2: 繁簡轉換
        final_text = traditional_to_simplified(dict_converted)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "original_text": original_text,
                "after_dict_conversion": dict_converted,
                "final_text": final_text,
                "opencc_available": OPENCC_AVAILABLE,
                "dict_applied": dict_converted != original_text,
                "simplified_applied": final_text != dict_converted
            }
        )
    except Exception as ex:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(ex)
            }
        )


@app.get("/processing_status")
async def get_processing_status():
    """獲取文字處理功能的狀態"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "opencc_available": OPENCC_AVAILABLE,
            "dict_count": len(custom_dict),
            "processing_pipeline": [
                "1. 自定義詞庫轉換",
                "2. 繁體轉簡體 (OpenCC)" if OPENCC_AVAILABLE else "2. 繁體轉簡體 (停用)"
            ]
        }
    )



@app.post("/audio/speech", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api_openai(request: Request):
    """ OpenAI competible API, see: https://api.openai.com/v1/audio/speech """
    try:
        data = await request.json()
        text = data["input"]
        character = data["voice"]
        #model param is omitted
        _model = data["model"]
        
        # 優先使用 API 請求中的 seed，否則使用 speaker 的預設 seed
        if "seed" in data:
            seed = data["seed"]
        else:
            seed = get_speaker_default_seed(character, fallback_seed=8)

        # 完整文字處理：詞庫轉換 + 繁簡轉換
        processed_text = process_text_for_tts(text)

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, processed_text, seed=seed)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=processed_text, target_sample_rate=16000)
        return Response(content=wav_bytes_16k, media_type="audio/wav")
    
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        print(tb_str)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )


@app.post("/tts_upload", responses={
    200: {"content": {"application/octet-stream": {}}},
    500: {"content": {"application/json": {}}}
})
async def tts_api_upload(
    text: str,
    audio_file: UploadFile = File(...),
    seed: int = 8
):
    """使用上傳的音檔進行 TTS 合成"""
    try:
        # 完整文字處理：詞庫轉換 + 繁簡轉換
        processed_text = process_text_for_tts(text)
        
        # 創建臨時目錄保存上傳的音檔
        temp_dir = "/tmp/audio_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成唯一的文件名
        file_extension = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".wav"
        temp_filename = f"{uuid.uuid4()}{file_extension}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        # 保存上傳的文件
        with open(temp_filepath, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        global tts
        sr, wav = await tts.infer([temp_filepath], processed_text, seed=seed)
        
        # 清理臨時文件
        try:
            os.remove(temp_filepath)
        except:
            pass
        
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=processed_text, target_sample_rate=16000)
        return Response(content=wav_bytes_16k, media_type="audio/wav")
    
    except Exception as ex:
        tb_str = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(tb_str)
            }
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=11996)
    parser.add_argument("--model_dir", type=str, default="/path/to/IndexTeam/Index-TTS")
    parser.add_argument("--gpu_memory_utilization", type=float, default=0.5)
    args = parser.parse_args()

    uvicorn.run(app=app, host=args.host, port=args.port)
