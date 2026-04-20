
import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "7"

import re
import asyncio
import io
import struct
import traceback
import tempfile
import uuid
import subprocess
from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse

import base64

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    print("asyncpg 未安裝，PostgreSQL 替換規則功能將被停用")
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
db_pool = None

# ── Admin auth ───────────────────────────────────────────────────────────────

def _check_admin_auth(request: Request) -> bool:
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        user, password = decoded.split(":", 1)
        return user == admin_user and password == admin_pass
    except Exception:
        return False

def _require_admin_auth(request: Request):
    if not _check_admin_auth(request):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Admin"'},
            content="Unauthorized",
        )
    return None

# ── Streaming helpers ────────────────────────────────────────────────────────

def make_wav_header(sample_rate=16000, channels=1, bits_per_sample=16):
    """Build a streaming-friendly WAV header with unknown data size (0xFFFFFFFF)."""
    data_size = 0xFFFFFFFF
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    return struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', data_size, b'WAVE',
        b'fmt ', 16, 1, channels, sample_rate,
        byte_rate, block_align, bits_per_sample,
        b'data', data_size,
    )

# ── PostgreSQL replacement rules ─────────────────────────────────────────────

def to_hans(text: str) -> str:
    """繁體轉簡體（供 DB 規則使用）"""
    if OPENCC_AVAILABLE and opencc_t2s:
        return opencc_t2s.convert(text)
    return text

def build_pattern_hans(pattern_orig: str, is_regex: bool) -> str:
    """is_regex=False 時用 re.escape 轉成字面比對；True 時直接轉簡體保留 regex 語法。"""
    if is_regex:
        return to_hans(pattern_orig)
    return re.escape(to_hans(pattern_orig))

async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS replacement_rules (
                id                   SERIAL PRIMARY KEY,
                set_name             VARCHAR(100) NOT NULL,
                pattern_original     TEXT NOT NULL,
                pattern_hans         TEXT NOT NULL,
                replacement_original TEXT NOT NULL,
                replacement_hans     TEXT NOT NULL,
                flags                TEXT[] DEFAULT '{}',
                is_regex             BOOLEAN DEFAULT FALSE,
                order_num            INT DEFAULT 0,
                created_at           TIMESTAMP DEFAULT NOW(),
                updated_at           TIMESTAMP DEFAULT NOW()
            )
        """)
        for col, definition in [
            ("pattern_original",     "TEXT NOT NULL DEFAULT ''"),
            ("pattern_hans",         "TEXT NOT NULL DEFAULT ''"),
            ("replacement_original", "TEXT NOT NULL DEFAULT ''"),
            ("replacement_hans",     "TEXT NOT NULL DEFAULT ''"),
            ("is_regex",             "BOOLEAN DEFAULT FALSE"),
        ]:
            await conn.execute(f"""
                ALTER TABLE replacement_rules
                ADD COLUMN IF NOT EXISTS {col} {definition}
            """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_replacement_rules_set_name
            ON replacement_rules(set_name, order_num)
        """)

async def apply_db_replacements(set_name: str, text: str) -> str:
    """套用替換規則：廠商組優先，全域組（_global_）後執行，組內按 pattern 長度降冪。"""
    if not db_pool:
        return text

    async def _apply_rows(rows, t: str) -> str:
        for row in rows:
            flag_val = 0
            for f in (row['flags'] or []):
                flag_val |= getattr(re, f, 0)
            t = re.sub(row['pattern_hans'], row['replacement_hans'], t, flags=flag_val)
        return t

    async with db_pool.acquire() as conn:
        if set_name and set_name != '_global_':
            # 廠商組先跑（長度降冪），全域組後跑（長度降冪）
            vendor_rows = await conn.fetch(
                "SELECT pattern_hans, replacement_hans, flags FROM replacement_rules "
                "WHERE set_name = $1 "
                "ORDER BY LENGTH(pattern_hans) DESC, order_num, id",
                set_name
            )
            global_rows = await conn.fetch(
                "SELECT pattern_hans, replacement_hans, flags FROM replacement_rules "
                "WHERE set_name = '_global_' "
                "ORDER BY LENGTH(pattern_hans) DESC, order_num, id"
            )
            text = await _apply_rows(vendor_rows, text)
            text = await _apply_rows(global_rows, text)
        elif set_name:
            rows = await conn.fetch(
                "SELECT pattern_hans, replacement_hans, flags FROM replacement_rules "
                "WHERE set_name = $1 "
                "ORDER BY LENGTH(pattern_hans) DESC, order_num, id",
                set_name
            )
            text = await _apply_rows(rows, text)
    return text

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts, db_pool
    cfg_path = os.path.join(args.model_dir, "config.yaml")
    tts = IndexTTS(model_dir=args.model_dir, cfg_path=cfg_path, gpu_memory_utilization=args.gpu_memory_utilization)

    # 載入自定義詞庫
    load_custom_dict()

    # 連線 PostgreSQL（可選，失敗不影響服務啟動）
    if ASYNCPG_AVAILABLE:
        try:
            db_url = (
                f"postgresql://{os.getenv('DB_USER', 'indextts')}:{os.getenv('DB_PASSWORD', 'indextts')}"
                f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
                f"/{os.getenv('DB_NAME', 'indextts')}"
            )
            db_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
            await init_db(db_pool)
            print("PostgreSQL 替換規則資料庫已連線")
        except Exception as e:
            print(f"PostgreSQL 連線失敗，替換規則功能停用: {e}")
            db_pool = None

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
    if db_pool:
        await db_pool.close()

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
        replacement_set = data.get("replacement", None)

        # DB 替換規則（可選）
        text = await apply_db_replacements(replacement_set, text)

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
        replacement_set = data.get("replacement", None)

        # 優先使用 API 請求中的 seed，否則使用 speaker 的預設 seed
        if "seed" in data:
            seed = data["seed"]
        else:
            seed = get_speaker_default_seed(character, fallback_seed=8)

        # DB 替換規則（可選）
        text = await apply_db_replacements(replacement_set, text)

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


# ── Streaming TTS endpoints ──────────────────────────────────────────────────

@app.post("/tts_stream")
async def tts_stream(request: Request):
    """串流 TTS（使用已註冊 speaker），逐句回傳 16kHz mono WAV PCM chunks。"""
    try:
        data = await request.json()
        text = data.get("text", "")
        character = data.get("character", "")
        replacement_set = data.get("replacement", None)

        text = await apply_db_replacements(replacement_set, text)
        processed_text = process_text_for_tts(text)

        global tts

        async def generate():
            yield make_wav_header(sample_rate=16000)
            async for wav_chunk in tts.infer_with_ref_audio_embed_stream(character, processed_text):
                yield wav_chunk.tobytes()

        return StreamingResponse(
            generate(),
            media_type="audio/wav",
            headers={"X-Sample-Rate": "16000", "X-Channels": "1"},
        )
    except Exception as ex:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "error": str(ex)})


@app.post("/tts_url_stream")
async def tts_url_stream(request: Request):
    """串流 TTS（使用音檔路徑），逐句回傳 16kHz mono WAV PCM chunks。"""
    try:
        data = await request.json()
        text = data.get("text", "")
        audio_paths = data.get("audio_paths", [])
        seed = data.get("seed", None)
        replacement_set = data.get("replacement", None)

        text = await apply_db_replacements(replacement_set, text)
        processed_text = process_text_for_tts(text)

        global tts

        async def generate():
            yield make_wav_header(sample_rate=16000)
            async for wav_chunk in tts.infer_stream(audio_paths, processed_text, seed=seed):
                yield wav_chunk.tobytes()

        return StreamingResponse(
            generate(),
            media_type="audio/wav",
            headers={"X-Sample-Rate": "16000", "X-Channels": "1"},
        )
    except Exception as ex:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "error": str(ex)})


# ── PostgreSQL replacement rules CRUD ────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def frontend():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.html")
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>test.html 不存在</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/vendorweb", response_class=HTMLResponse)
async def vendor_web():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor_web.html")
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>vendor_web.html 不存在</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/replacementweb")
async def replacement_web(request: Request):
    denied = _require_admin_auth(request)
    if denied:
        return denied
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replacement_web.html")
    if not os.path.exists(html_path):
        return HTMLResponse("<h1>replacement_web.html 不存在</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/replacements")
async def list_sets(hide_global: bool = False):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT set_name, COUNT(*) AS rule_count "
            "FROM replacement_rules GROUP BY set_name ORDER BY set_name"
        )
    result = [dict(r) for r in rows]
    if hide_global:
        result = [r for r in result if r["set_name"] != "_global_"]
    return result

@app.get("/replacements/{set_name}")
async def list_rules(set_name: str):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, set_name, pattern_original AS pattern, replacement_original AS replacement, "
            "flags, is_regex, order_num "
            "FROM replacement_rules WHERE set_name = $1 ORDER BY order_num, id",
            set_name
        )
    return [dict(r) for r in rows]

@app.post("/replacements/{set_name}")
async def add_rule(set_name: str, request: Request):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    data = await request.json()
    pattern_orig = data["pattern"]
    replacement_orig = data["replacement"]
    is_regex = data.get("is_regex", False)
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO replacement_rules "
            "(set_name, pattern_original, pattern_hans, replacement_original, replacement_hans, flags, is_regex, order_num) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) "
            "RETURNING id, set_name, pattern_original AS pattern, replacement_original AS replacement, flags, is_regex, order_num",
            set_name,
            pattern_orig,
            build_pattern_hans(pattern_orig, is_regex),
            replacement_orig,
            to_hans(replacement_orig),
            data.get("flags", []),
            is_regex,
            data.get("order_num", 0),
        )
    return dict(row)

@app.put("/replacements/{set_name}/{rule_id}")
async def update_rule(set_name: str, rule_id: int, request: Request):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    data = await request.json()
    pattern_orig = data["pattern"]
    replacement_orig = data["replacement"]
    is_regex = data.get("is_regex", False)
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE replacement_rules "
            "SET pattern_original=$1, pattern_hans=$2, replacement_original=$3, replacement_hans=$4, "
            "flags=$5, is_regex=$6, order_num=$7, updated_at=NOW() "
            "WHERE id=$8 AND set_name=$9 "
            "RETURNING id, set_name, pattern_original AS pattern, replacement_original AS replacement, flags, is_regex, order_num",
            pattern_orig,
            build_pattern_hans(pattern_orig, is_regex),
            replacement_orig,
            to_hans(replacement_orig),
            data.get("flags", []),
            is_regex,
            data.get("order_num", 0),
            rule_id,
            set_name,
        )
    if not row:
        return JSONResponse(status_code=404, content={"error": "rule not found"})
    return dict(row)

@app.delete("/replacements/{set_name}/{rule_id}")
async def delete_rule(set_name: str, rule_id: int):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM replacement_rules WHERE id=$1 AND set_name=$2",
            rule_id, set_name
        )
    deleted = int(result.split()[-1])
    if deleted == 0:
        return JSONResponse(status_code=404, content={"error": "rule not found"})
    return {"deleted": rule_id}

@app.get("/replacements/{set_name}/export")
async def export_rules(set_name: str):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT pattern_original AS pattern, replacement_original AS replacement, "
            "flags, is_regex, order_num "
            "FROM replacement_rules WHERE set_name = $1 ORDER BY order_num, id",
            set_name
        )
    data = [dict(r) for r in rows]
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{set_name}_rules.json"'},
    )

@app.post("/replacements/{set_name}/bulk")
async def bulk_import_rules(set_name: str, request: Request, mode: str = "overwrite"):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    rules = await request.json()
    async with db_pool.acquire() as conn:
        if mode == "overwrite":
            await conn.execute("DELETE FROM replacement_rules WHERE set_name=$1", set_name)
            start_order = 0
        else:
            existing = await conn.fetch(
                "SELECT pattern_original FROM replacement_rules WHERE set_name=$1", set_name
            )
            existing_patterns = {r["pattern_original"] for r in existing}
            rules = [r for r in rules if r["pattern"] not in existing_patterns]
            max_order = await conn.fetchval(
                "SELECT COALESCE(MAX(order_num), -1) FROM replacement_rules WHERE set_name=$1", set_name
            )
            start_order = max_order + 1

        await conn.executemany(
            "INSERT INTO replacement_rules "
            "(set_name, pattern_original, pattern_hans, replacement_original, replacement_hans, flags, is_regex, order_num) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            [
                (
                    set_name,
                    r["pattern"],
                    build_pattern_hans(r["pattern"], r.get("is_regex", False)),
                    r["replacement"],
                    to_hans(r["replacement"]),
                    r.get("flags", []),
                    r.get("is_regex", False),
                    start_order + i,
                )
                for i, r in enumerate(rules)
            ]
        )
    return {"imported": len(rules), "set_name": set_name, "mode": mode}

@app.post("/replacements/{new_set}/clone/{source_set}")
async def clone_rules(new_set: str, source_set: str, mode: str = "overwrite"):
    if not db_pool:
        return JSONResponse(status_code=503, content={"error": "PostgreSQL 未連線"})
    async with db_pool.acquire() as conn:
        source_rows = await conn.fetch(
            "SELECT pattern_original, pattern_hans, replacement_original, replacement_hans, "
            "flags, is_regex, order_num "
            "FROM replacement_rules WHERE set_name = $1 ORDER BY order_num, id",
            source_set
        )
        if not source_rows:
            return JSONResponse(status_code=404, content={"error": f"source set '{source_set}' not found or empty"})

        if mode == "overwrite":
            await conn.execute("DELETE FROM replacement_rules WHERE set_name=$1", new_set)
            rows_to_insert = source_rows
            start_order = 0
        else:
            existing = await conn.fetch(
                "SELECT pattern_original FROM replacement_rules WHERE set_name=$1", new_set
            )
            existing_patterns = {r["pattern_original"] for r in existing}
            rows_to_insert = [r for r in source_rows if r["pattern_original"] not in existing_patterns]
            max_order = await conn.fetchval(
                "SELECT COALESCE(MAX(order_num), -1) FROM replacement_rules WHERE set_name=$1", new_set
            )
            start_order = max_order + 1

        await conn.executemany(
            "INSERT INTO replacement_rules "
            "(set_name, pattern_original, pattern_hans, replacement_original, replacement_hans, flags, is_regex, order_num) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
            [
                (
                    new_set,
                    r["pattern_original"],
                    r["pattern_hans"],
                    r["replacement_original"],
                    r["replacement_hans"],
                    list(r["flags"]) if r["flags"] else [],
                    r["is_regex"],
                    start_order + i,
                )
                for i, r in enumerate(rows_to_insert)
            ]
        )
    return {"cloned": len(rows_to_insert), "source": source_set, "target": new_set, "mode": mode}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=11996)
    parser.add_argument("--model_dir", type=str, default="/path/to/IndexTeam/Index-TTS")
    parser.add_argument("--gpu_memory_utilization", type=float, default=0.5)
    args = parser.parse_args()

    uvicorn.run(app=app, host=args.host, port=args.port)
