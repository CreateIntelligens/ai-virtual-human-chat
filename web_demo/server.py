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

async def call_asr_api(audio_data):
    # 调用ASR完成语音识别
    answer = "语音已收到，这里只是模仿，真正对话需要您自己设置ASR服务。"
    return answer

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

# ==================== 健康檢查和狀態 ====================

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    providers = dual_tts_manager.get_available_providers()
    return {
        "status": "healthy",
        "tts_engines": providers,
        "total_engines": len(providers),
        "available_engines": len([p for p in providers if p["status"] == "available"])
    }

@app.get("/")
async def root():
    """根路徑重定向到測試頁面"""
    return RedirectResponse(url="/static/test_dialog_api.html")

# 启动Uvicorn服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
