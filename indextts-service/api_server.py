
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

    current_file_path = os.path.abspath(__file__)
    cur_dir = os.path.dirname(current_file_path)
    speaker_path = os.path.join(cur_dir, "assets/speaker.json")
    if os.path.exists(speaker_path):
        speaker_dict = json.load(open(speaker_path, 'r'))

        for speaker, audio_paths in speaker_dict.items():
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

        global tts
        sr, wav = await tts.infer(audio_paths, text, seed=seed)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=text, target_sample_rate=16000)
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

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, text)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=text, target_sample_rate=16000)
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

        global tts
        sr, wav = await tts.infer_with_ref_audio_embed(character, text)
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=text, target_sample_rate=16000)
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
        sr, wav = await tts.infer([temp_filepath], text, seed=seed)
        
        # 清理臨時文件
        try:
            os.remove(temp_filepath)
        except:
            pass
        
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, wav, sr, format='WAV')
            wav_bytes = wav_buffer.getvalue()
        
        # 使用ffmpeg轉換為16kHz
        wav_bytes_16k = convert_audio_with_ffmpeg(wav_bytes, text=text, target_sample_rate=16000)
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
