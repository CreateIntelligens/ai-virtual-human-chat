import json
import requests
import asyncio
import re
import base64
import tempfile
import os
from fastapi.responses import StreamingResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 導入雙引擎 TTS 管理器
from voiceapi.dual_tts_manager import dual_tts_manager

# SenseVoice STT 服務配置
SENSEVOICE_API_URL = os.getenv("SENSEVOICE_API_URL", "http://sensevoice-service:50002")
SENSEVOICE_ENABLED = os.getenv("SENSEVOICE_ENABLED", "true").lower() == "true"
SENSEVOICE_API_TIMEOUT = int(os.getenv("SENSEVOICE_API_TIMEOUT", "30"))

app = FastAPI()

# 添加 CORS 中間件以解決跨域問題
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="web_demo/static"), name="static")

# ==================== 雙引擎 TTS 系統 ====================

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 TTS 引擎"""
    print("🚀 正在初始化雙引擎 TTS 系統...")
    await dual_tts_manager.initialize()
    print("✅ 雙引擎 TTS 系統初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時清理資源"""
    print("🔄 正在關閉 TTS 引擎...")
    await dual_tts_manager.close()
    print("✅ TTS 引擎已關閉")

# ==================== TTS API 端點 ====================

@app.get("/tts/providers")
async def get_tts_providers():
    """獲取可用的 TTS 引擎列表"""
    return {
        "providers": dual_tts_manager.get_available_providers(),
        "default_provider": dual_tts_manager.default_provider
    }

@app.get("/tts/voices")
async def get_all_voices():
    """獲取所有引擎的聲音列表"""
    return dual_tts_manager.get_all_voices()

@app.get("/tts/voices/{provider}")
async def get_provider_voices(provider: str):
    """獲取指定引擎的聲音列表"""
    voices = dual_tts_manager.get_provider_voices(provider)
    if not voices:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not found or unavailable")
    return voices

@app.post("/tts/generate")
async def generate_tts_audio(request: Request):
    """生成 TTS 音頻"""
    try:
        body = await request.json()
        text = body.get("text", "")
        provider = body.get("provider")  # 可選，不指定則使用默認引擎
        voice_id = body.get("voice_id", "female-tianmei")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # 使用雙引擎管理器生成音頻
        audio_base64 = await dual_tts_manager.generate_audio(
            text=text,
            provider=provider,
            voice_id=voice_id
        )
        
        if audio_base64:
            return {
                "success": True,
                "audio": audio_base64,
                "provider_used": provider or dual_tts_manager.default_provider,
                "voice_id": voice_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 向後兼容的 TTS 函數 ====================

async def get_audio_async(text_cache, voice_speed, voice_id):
    """異步版本的音頻生成函數（向後兼容）"""
    try:
        # 使用雙引擎管理器生成音頻
        return await dual_tts_manager.generate_audio(
            text=text_cache,
            voice_id=voice_id
        )
    except Exception as e:
        print(f"❌ TTS 生成失敗: {e}")
        return None

def get_fallback_audio():
    """降級處理 - 跳過音頻生成"""
    print("⚠️ TTS失敗，跳過音頻生成（避免播放不相關音頻）")
    return None

def get_audio(text_cache, voice_speed, voice_id):
    """向後兼容的音頻生成函數（同步版本，用於向後兼容）"""
    return get_fallback_audio()

# ==================== LLM 和對話處理 ====================

# 導入LLM模組
from voiceapi.llm import llm_answer, llm_stream

def llm_answer_local(prompt):
    """本地LLM回答函數（向後兼容）"""
    return llm_answer(prompt)

def split_sentence(sentence, min_length=10):
    print(f"📝 分割文本: '{sentence}' (長度: {len(sentence)}, 最小長度: {min_length})")
    
    # 如果文本很短，直接返回不分割
    if len(sentence) <= 30:
        print(f"📝 文本較短，不分割: ['{sentence}']")
        return [sentence]
    
    # 定义包括小括号在内的主要标点符号
    punctuations = r'[。？！；…，、()（）]'
    # 使用正则表达式切分句子，保留标点符号
    parts = re.split(f'({punctuations})', sentence)
    parts = [p for p in parts if p]  # 移除空字符串
    print(f"📝 初始分割: {parts}")
    
    sentences = []
    current = ''
    for part in parts:
        if current:
            # 如果当前片段加上新片段长度超过最小长度，则将当前片段添加到结果中
            if len(current) + len(part) >= min_length:
                sentences.append(current + part)
                current = ''
            else:
                current += part
        else:
            current = part
    # 将剩余的片段添加到结果中
    if len(current) >= 2:
        sentences.append(current)
    
    print(f"📝 最終分割結果: {sentences}")
    return sentences

async def gen_stream(prompt, asr=False, voice_speed=None, voice_id=None, provider=None):
    """生成流式響應"""
    print(f"🎯 流式生成參數: voice_speed={voice_speed}, voice_id={voice_id}, provider={provider}")
    
    try:
        if asr:
            chunk = {
                "prompt": prompt
            }
            yield f"{json.dumps(chunk)}\n"  # 使用换行符分隔 JSON 块

        # 特殊處理 "." 輸入，避免 LLM 也回應 "."
        if prompt.strip() == ".":
            print("🔇 檢測到 '.' 輸入，提供友善提示")
            text_cache = "我沒有聽清楚您說什麼，請您再說一遍好嗎？"
        else:
            text_cache = llm_answer(prompt)
            
        sentences = split_sentence(text_cache)

        for index_, sub_text in enumerate(sentences):
            try:
                # 使用雙引擎管理器生成音頻
                base64_string = await dual_tts_manager.generate_audio(
                    text=sub_text,
                    provider=provider,
                    voice_id=voice_id or "female-tianmei"
                )
                
                # 生成 JSON 格式的数据块
                chunk = {
                    "text": sub_text,
                    "audio": base64_string,
                    "endpoint": index_ == len(sentences)-1
                }
                yield f"{json.dumps(chunk)}\n"  # 使用换行符分隔 JSON 块
                await asyncio.sleep(0.2)  # 模拟异步延迟
                
            except Exception as e:
                print(f"❌ 生成音頻失敗 (片段 {index_}): {e}")
                # 即使音頻生成失敗，也要發送文本響應
                chunk = {
                    "text": sub_text,
                    "audio": None,  # 音頻失敗時設為 None
                    "endpoint": index_ == len(sentences)-1,
                    "error": f"TTS 生成失敗: {str(e)}"
                }
                yield f"{json.dumps(chunk)}\n"
                await asyncio.sleep(0.2)
                
    except Exception as e:
        print(f"❌ 流式響應生成失敗: {e}")
        # 發送錯誤響應並正確結束流
        error_chunk = {
            "text": "",
            "audio": None,
            "endpoint": True,
            "error": f"流式響應失敗: {str(e)}"
        }
        yield f"{json.dumps(error_chunk)}\n"

# ==================== 對話 API 端點 ====================

# 处理 ASR 和 TTS 的端点
@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    # 模仿调用 ASR API 获取文本
    text = "语音已收到，这里只是模仿，真正对话需要您自己设置ASR服务。"
    # 调用 TTS 生成流式响应
    return StreamingResponse(gen_stream(text, asr=True), media_type="application/json")

def post_process_transcription(text):
    """對 SenseVoice 識別結果進行後處理"""
    if not text:
        return text
    
    # 如果整個文字只是一個中文句號，改為英文點號
    if text.strip() == "。":
        print(f"📝 純句號轉換: '。' -> '.'")
        return "."
    
    # 如果文字以中文句號結尾，移除它
    if text.endswith("。"):
        processed_text = text[:-1]
        print(f"📝 移除結尾句號: '{text}' -> '{processed_text}'")
        return processed_text
    
    return text

def is_valid_transcription(text):
    """判斷語音識別結果是否有效，過濾常見的誤識別"""
    if not text or not text.strip():
        return False
    
    # 常見的誤識別單詞（靜音或噪音時容易出現）
    false_positives = [
        "okay", "ok", "the", "yes", "no", "a", "an", "i", "you", "we", "they",
        "okay.", "ok.", "the.", "yes.", "no.", "a.", "an.", "i.", "you.", "we.", "they.",
        "um", "uh", "er", "ah", "oh", "and", "or", "but", "so", "well",
        "um.", "uh.", "er.", "ah.", "oh.", "and.", "or.", "but.", "so.", "well."
    ]
    
    cleaned_text = text.lower().strip()
    
    # 如果是常見誤識別且很短，視為無效
    if cleaned_text in false_positives and len(cleaned_text) <= 5:
        print(f"🚫 過濾誤識別結果: '{text}' -> 改為 '.'")
        return False
    
    # 如果只有標點符號，視為無效
    if all(c in '.,!?;:' for c in cleaned_text):
        print(f"🚫 過濾純標點符號: '{text}' -> 改為 '.'")
        return False
        
    return True

async def call_sensevoice_api(audio_data):
    """調用 SenseVoice API 進行語音識別"""
    try:
        print("🎤 正在調用 SenseVoice API 進行語音識別...")
        
        # 準備文件上傳
        files = {
            'files': ('audio.wav', audio_data, 'audio/wav')
        }
        data = {
            'keys': 'audio',
            'lang': 'zh'  # 自動檢測語言
        }
        
        # 調用 SenseVoice API
        response = requests.post(
            f"{SENSEVOICE_API_URL}/api/v1/asr",
            files=files,
            data=data,
            timeout=SENSEVOICE_API_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 記錄完整的 SenseVoice 回應（用於調試）
            print(f"🔍 SenseVoice 完整回應: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('result') and len(result['result']) > 0:
                # 獲取識別結果
                transcription = result['result'][0].get('clean_text', '').strip()
                
                # 添加後處理
                transcription = post_process_transcription(transcription)
                
                if transcription and is_valid_transcription(transcription):
                    print(f"✅ 語音識別成功: {transcription}")
                    return transcription
                else:
                    print("🔇 未檢測到有效語音內容，返回 '.'")
                    return "."
            else:
                print("🔇 語音識別結果為空，返回 '.'")
                return "."
        else:
            print(f"❌ SenseVoice API 調用失敗: {response.status_code}")
            return "."  # API 失敗也返回 "."，保持流程連續性
            
    except requests.exceptions.Timeout:
        print("❌ SenseVoice API 調用超時")
        return "."  # 超時也返回 "."
    except Exception as e:
        print(f"❌ SenseVoice API 調用錯誤: {e}")
        return "."  # 任何錯誤都返回 "."

async def call_asr_api(audio_data):
    """向後兼容的 ASR API 調用（現在使用 SenseVoice）"""
    return await call_sensevoice_api(audio_data)

@app.post("/eb_stream")    # 前端调用的path
async def eb_stream(request: Request):
    try:
        body = await request.json()
        input_mode = body.get("input_mode")
        voice_speed = body.get("voice_speed")
        voice_id = body.get("voice_id")
        provider = body.get("provider")  # 新增：支援指定 TTS 引擎

        if input_mode == "audio":
            base64_audio = body.get("audio")
            # 解码 Base64 音频数据
            audio_data = base64.b64decode(base64_audio)
            # 这里可以添加对音频数据的处理逻辑
            prompt = await call_asr_api(audio_data)  # 假设 call_asr_api 可以处理音频数据
            return StreamingResponse(
                gen_stream(prompt, asr=True, voice_speed=voice_speed, voice_id=voice_id, provider=provider), 
                media_type="application/json"
            )
        elif input_mode == "text":
            prompt = body.get("prompt")
            return StreamingResponse(
                gen_stream(prompt, asr=False, voice_speed=voice_speed, voice_id=voice_id, provider=provider), 
                media_type="application/json"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid input mode")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STT API 端點 ====================

@app.post("/stt/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """語音轉文字端點"""
    try:
        # 讀取上傳的音頻文件
        audio_data = await file.read()
        
        # 調用 SenseVoice API
        transcription = await call_sensevoice_api(audio_data)
        
        return {
            "success": True,
            "transcription": transcription,
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 處理失敗: {str(e)}")

# 注意：/voice_chat 端點已移除，現在語音對話流程為：
# 1. 前端調用 /stt/transcribe 進行語音轉文字
# 2. 前端獲得文字後，直接復用 /eb_stream 進行文字對話
# 這樣確保語音對話與純文字對話使用完全相同的處理流程

# ==================== 健康檢查和狀態 ====================

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    providers = dual_tts_manager.get_available_providers()
    
    # 檢查 SenseVoice 服務狀態
    sensevoice_status = "unknown"
    try:
        response = requests.get(f"{SENSEVOICE_API_URL}/", timeout=5)
        sensevoice_status = "available" if response.status_code == 200 else "unavailable"
    except:
        sensevoice_status = "unavailable"
    
    return {
        "status": "healthy",
        "tts_engines": providers,
        "total_engines": len(providers),
        "available_engines": len([p for p in providers if p["status"] == "available"]),
        "stt_service": {
            "name": "SenseVoice",
            "status": sensevoice_status,
            "url": SENSEVOICE_API_URL
        }
    }

@app.get("/")
async def root():
    """根路徑重定向到測試頁面"""
    return RedirectResponse(url="/static/test_dialog_api.html")

# 启动Uvicorn服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
