# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys

# Fix DeepSpeed CUDA check issue before importing any transformers modules
os.environ['DS_BUILD_OPS'] = '0'
os.environ['DS_BUILD_FUSED_ADAM'] = '0'
os.environ['DS_BUILD_CPU_ADAM'] = '0'
os.environ['DS_BUILD_UTILS'] = '0'

# Fix MKL threading layer conflict
os.environ['MKL_THREADING_LAYER'] = 'GNU'
os.environ['MKL_SERVICE_FORCE_INTEL'] = '1'

import argparse
import logging
import json
import time

# 配置日誌格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 降低其他模組的日誌級別
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import io
import wave
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/../../..'.format(ROOT_DIR))
sys.path.append('{}/../../../third_party/Matcha-TTS'.format(ROOT_DIR))

# Register custom vLLM model before importing CosyVoice
try:
    from vllm import ModelRegistry
    from cosyvoice.vllm.cosyvoice2 import CosyVoice2ForCausalLM
    ModelRegistry.register_model("CosyVoice2ForCausalLM", CosyVoice2ForCausalLM)
    logging.info("Successfully registered CosyVoice2ForCausalLM with vLLM")
except ImportError:
    logging.warning("vLLM not available, skipping custom model registration")

from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
from cosyvoice.utils.common import set_all_random_seed

app = FastAPI()
# set cross region allowance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


def generate_data(model_output):
    for i in model_output:
        tts_audio = (i['tts_speech'].numpy() * (2 ** 15)).astype(np.int16).tobytes()
        yield tts_audio


def load_voice_config():
    """載入聲音配置檔案，優先使用 local 配置"""
    local_config_path = os.path.join(ROOT_DIR, '../../../config/voices.local.json')
    example_config_path = os.path.join(ROOT_DIR, '../../../config/voices.example.json')
    
    # 優先讀取 local 配置
    if os.path.exists(local_config_path):
        config_path = local_config_path
        print(f"使用個人配置: {config_path}")
    else:
        config_path = example_config_path
        print(f"使用範例配置: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="聲音配置檔案不存在")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="聲音配置檔案格式錯誤")


def get_voice_by_id(voice_id):
    """根據 voice_id 獲取聲音配置"""
    config = load_voice_config()
    for voice in config['voices']:
        if voice['id'] == voice_id:
            return voice
    raise HTTPException(status_code=404, detail=f"找不到聲音配置: {voice_id}")


def load_audio_sample(audio_file):
    """載入語音樣本檔案"""
    audio_path = os.path.join(ROOT_DIR, '../../../config/audio_samples', audio_file)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"語音樣本檔案不存在: {audio_file}")
    return load_wav(audio_path, 16000)


@app.get("/inference_sft")
@app.post("/inference_sft")
async def inference_sft(tts_text: str = Form(), spk_id: str = Form()):
    model_output = cosyvoice.inference_sft(tts_text, spk_id)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_zero_shot")
@app.post("/inference_zero_shot")
async def inference_zero_shot(tts_text: str = Form(), prompt_text: str = Form(), prompt_wav: UploadFile = File(), seed: int = Form(0)):
    set_all_random_seed(seed)
    print(f"種子碼: {seed}")
    prompt_speech_16k = load_wav(prompt_wav.file, 16000)
    model_output = cosyvoice.inference_zero_shot(tts_text, prompt_text, prompt_speech_16k)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_zero_shot_wav")
@app.post("/inference_zero_shot_wav")
async def inference_zero_shot_wav(tts_text: str = Form(), prompt_text: str = Form(), prompt_wav: UploadFile = File(), seed: int = Form(0)):
    set_all_random_seed(seed)
    print(f"種子碼: {seed}")
    prompt_speech_16k = load_wav(prompt_wav.file, 16000)
    model_output = cosyvoice.inference_zero_shot(tts_text, prompt_text, prompt_speech_16k)
    
    # 將模型輸出轉換為WAV格式
    audio_data = []
    for i in model_output:
        # tts_speech 的形狀是 (1, n_samples),需要展平為 (n_samples,)
        audio_data.append(i['tts_speech'].numpy().flatten())
    
    # 合併所有音頻數據
    if audio_data:
        combined_audio = np.concatenate(audio_data)
        # 轉換為16位整數格式
        audio_int16 = (combined_audio * (2 ** 15)).astype(np.int16)
        
        # 創建WAV檔案
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # 單聲道
            wav_file.setsampwidth(2)  # 16位 = 2字節
            wav_file.setframerate(22050)  # 採樣率，與load_wav的採樣率一致
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_buffer.seek(0)
        return Response(
            content=wav_buffer.getvalue(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=output.wav"}
        )
    else:
        return Response(content=b"", media_type="audio/wav")


@app.get("/voices")
async def get_voices():
    """獲取可用的聲音配置列表"""
    try:
        config = load_voice_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inference_with_voice_config")
@app.post("/inference_with_voice_config")
async def inference_with_voice_config(tts_text: str = Form(), voice_id: str = Form(), original_text: str = Form(None)):
    """使用預配置聲音進行語音合成"""
    try:
        # 記錄開始時間
        start_time = time.time()
        
        # 獲取聲音配置
        voice_config = get_voice_by_id(voice_id)
        
        # 記錄原始文字和轉換後的文字
        print("\n" + "="*60)
        if original_text and original_text != tts_text:
            print(f"🎙️  語音生成請求")
            print(f"原始文字: {original_text}")
            print(f"台語文字: {tts_text}")
            print(f"使用聲音: {voice_config['name']} ({voice_id})")
        else:
            print(f"🎙️  語音生成請求")
            print(f"輸入文字: {tts_text}")
            print(f"使用聲音: {voice_config['name']} ({voice_id})")
        print("="*60)
        
        # 設定隨機種子
        seed = voice_config.get('seed', 0)
        set_all_random_seed(seed)
        
        # 載入語音樣本
        prompt_speech_16k = load_audio_sample(voice_config['audio_file'])
        
        # 進行語音合成
        model_output = cosyvoice.inference_zero_shot(
            tts_text, 
            voice_config['prompt_text'], 
            prompt_speech_16k
        )
        
        # 將模型輸出轉換為WAV格式
        audio_data = []
        for i in model_output:
            # tts_speech 的形狀是 (1, n_samples),需要展平為 (n_samples,)
            audio_data.append(i['tts_speech'].numpy().flatten())
        
        # 合併所有音頻數據
        if audio_data:
            combined_audio = np.concatenate(audio_data)
            # 轉換為16位整數格式
            audio_int16 = (combined_audio * (2 ** 15)).astype(np.int16)
            
            # 創建WAV檔案
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 單聲道
                wav_file.setsampwidth(2)  # 16位 = 2字節
                wav_file.setframerate(22050)  # 採樣率
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            
            # 記錄結束時間和總耗時
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"✅ 語音生成完成,耗時: {elapsed_time:.2f} 秒")
            print("="*60 + "\n")
            
            return Response(
                content=wav_buffer.getvalue(),
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename={voice_id}_output.wav"}
            )
        else:
            return Response(content=b"", media_type="audio/wav")
            
    except Exception as e:
        print(f"❌ 語音合成錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")


@app.get("/inference_cross_lingual")
@app.post("/inference_cross_lingual")
async def inference_cross_lingual(tts_text: str = Form(), prompt_wav: UploadFile = File()):
    prompt_speech_16k = load_wav(prompt_wav.file, 16000)
    model_output = cosyvoice.inference_cross_lingual(tts_text, prompt_speech_16k)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_instruct")
@app.post("/inference_instruct")
async def inference_instruct(tts_text: str = Form(), spk_id: str = Form(), instruct_text: str = Form()):
    model_output = cosyvoice.inference_instruct(tts_text, spk_id, instruct_text)
    return StreamingResponse(generate_data(model_output))


@app.get("/inference_instruct2")
@app.post("/inference_instruct2")
async def inference_instruct2(tts_text: str = Form(), instruct_text: str = Form(), prompt_wav: UploadFile = File()):
    prompt_speech_16k = load_wav(prompt_wav.file, 16000)
    model_output = cosyvoice.inference_instruct2(tts_text, instruct_text, prompt_speech_16k)
    return StreamingResponse(generate_data(model_output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',
                        type=int,
                        default=50005)
    parser.add_argument('--model_dir',
                        type=str,
                        default='iic/CosyVoice-300M',
                        help='local path or modelscope repo id')
    parser.add_argument('--load_vllm',
                        action='store_true',
                        help='enable vllm acceleration for faster inference')
    args = parser.parse_args()
    try:
        cosyvoice = CosyVoice(args.model_dir)
    except Exception:
        try:
            cosyvoice = CosyVoice2(args.model_dir, load_vllm=args.load_vllm)
        except Exception:
            raise TypeError('no valid model_type!')
    uvicorn.run(app, host="0.0.0.0", port=args.port)
