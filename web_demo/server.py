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

# 嘗試導入edge-tts，如果失敗則使用測試音檔
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    print("✅ Edge-TTS 可用")
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("❌ Edge-TTS 不可用，將使用測試音檔")

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

# ==================== 語音配置 ====================

# 音色映射表
VOICE_MAPPING = {
    "male-qn-qingse": "zh-CN-YunxiNeural",        # 青澀男
    "male-qn-badao": "zh-CN-YunyangNeural",       # 霸氣男
    "wumei_yujie": "zh-CN-XiaoxiaoNeural",        # 嫵媚女
    "female-tianmei": "zh-CN-XiaoyiNeural"        # 甜美女
}

async def generate_tts_with_edge_tts(text, voice_id):
    """使用edge-tts生成語音（如果可用）"""
    if not EDGE_TTS_AVAILABLE:
        return get_fallback_audio()
    
    try:
        voice_name = VOICE_MAPPING.get(voice_id, "zh-CN-XiaoxiaoNeural")
        print(f"🎵 使用Edge-TTS: '{text}' (長度: {len(text)}) -> {voice_name}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_filename = tmp_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as converted_file:
            converted_filename = converted_file.name
        
        # 生成Edge-TTS音頻
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(tmp_filename)
        
        # 轉換為16kHz單聲道以匹配原始格式
        import subprocess
        conversion_result = subprocess.run([
            'ffmpeg', '-y', '-i', tmp_filename, 
            '-ar', '16000',  # 採樣率 16kHz
            '-ac', '1',      # 單聲道
            '-sample_fmt', 's16',  # 16位PCM
            converted_filename
        ], capture_output=True, text=True)
        
        if conversion_result.returncode != 0:
            print(f"⚠️ 音頻轉換失敗，使用原始格式: {conversion_result.stderr}")
            audio_filename = tmp_filename
        else:
            print("✅ 音頻已轉換為16kHz單聲道")
            audio_filename = converted_filename
        
        with open(audio_filename, "rb") as audio_file:
            audio_data = audio_file.read()
        
        # 清理臨時文件
        os.unlink(tmp_filename)
        if os.path.exists(converted_filename):
            os.unlink(converted_filename)
        
        base64_string = base64.b64encode(audio_data).decode('utf-8')
        print(f"🔊 TTS生成成功: {len(audio_data)} bytes")
        return base64_string
        
    except Exception as e:
        print(f"❌ Edge-TTS失敗: {e}")
        return get_fallback_audio()

def get_fallback_audio():
    """降級處理 - 跳過音頻生成"""
    print("⚠️ TTS失敗，跳過音頻生成（避免播放不相關音頻）")
    return None

def get_audio(text_cache, voice_speed, voice_id):
    """向後兼容的音頻生成函數（同步版本，用於向後兼容）"""
    return get_fallback_audio()

async def get_audio_async(text_cache, voice_speed, voice_id):
    """異步版本的音頻生成函數"""
    if EDGE_TTS_AVAILABLE:
        return await generate_tts_with_edge_tts(text_cache, voice_id)
    else:
        return get_fallback_audio()

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


import asyncio
async def gen_stream(prompt, asr = False, voice_speed=None, voice_id=None):
    print("XXXXXXXXX", voice_speed, voice_id)
    if asr:
        chunk = {
            "prompt": prompt
        }
        yield f"{json.dumps(chunk)}\n"  # 使用换行符分隔 JSON 块

    text_cache = llm_answer(prompt)
    sentences = split_sentence(text_cache)

    for index_, sub_text in enumerate(sentences):
        base64_string = await get_audio_async(sub_text, voice_speed, voice_id)
        # 生成 JSON 格式的数据块
        chunk = {
            "text": sub_text,
            "audio": base64_string,
            "endpoint": index_ == len(sentences)-1
        }
        yield f"{json.dumps(chunk)}\n"  # 使用换行符分隔 JSON 块
        await asyncio.sleep(0.2)  # 模拟异步延迟

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

        if input_mode == "audio":
            base64_audio = body.get("audio")
            # 解码 Base64 音频数据
            audio_data = base64.b64decode(base64_audio)
            # 这里可以添加对音频数据的处理逻辑
            prompt = await call_asr_api(audio_data)  # 假设 call_asr_api 可以处理音频数据
            return StreamingResponse(gen_stream(prompt, asr=True, voice_speed=voice_speed, voice_id=voice_id), media_type="application/json")
        elif input_mode == "text":
            prompt = body.get("prompt")
            return StreamingResponse(gen_stream(prompt, asr=False, voice_speed=voice_speed, voice_id=voice_id), media_type="application/json")
        else:
            raise HTTPException(status_code=400, detail="Invalid input mode")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 启动Uvicorn服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
