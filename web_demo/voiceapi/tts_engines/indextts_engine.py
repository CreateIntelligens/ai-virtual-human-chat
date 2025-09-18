"""
IndexTTS VLLM 引擎實現 - 基於新版 IndexTTS VLLM API 調用方式
"""
import os
import json
import base64
import asyncio
import aiohttp
import tempfile
import subprocess
from io import BytesIO
from typing import Optional, Dict, Any
from .base_tts import BaseTTSEngine


class IndexTTSEngine(BaseTTSEngine):
    """IndexTTS VLLM 引擎實現 - 通過新版 API 調用"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base_url = None
        self.session = None
        
    async def initialize(self) -> bool:
        """初始化 IndexTTS VLLM 引擎"""
        try:
            # 從配置文件獲取 API 地址 - 修正配置路徑
            provider_info = self.config.get('provider_info', {})
            api_config = provider_info.get('api_config', {})
            self.api_base_url = api_config.get('base_url', 'http://indextts-service:8001')
            
            # 也支援環境變數覆蓋
            self.api_base_url = os.getenv('INDEXTTS_API_URL', self.api_base_url)
            
            print(f"🔧 IndexTTS API URL: {self.api_base_url}")
            
            # 創建 HTTP 會話
            self.session = aiohttp.ClientSession()
            
            # 測試 API 連接
            health_check = await self._check_api_health()
            if health_check:
                self.is_available = True
                print(f"✅ IndexTTS VLLM API 連接成功: {self.api_base_url}")
                return True
            else:
                print(f"❌ IndexTTS VLLM API 無法連接: {self.api_base_url}")
                return False
                
        except Exception as e:
            print(f"❌ IndexTTS VLLM 初始化失敗: {e}")
            return False
    
    async def _check_api_health(self) -> bool:
        """檢查 IndexTTS VLLM API 健康狀態"""
        try:
            # 使用新的健康檢查端點
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.get(f"{self.api_base_url}/health", timeout=timeout) as response:
                return response.status == 200
        except Exception as e:
            print(f"❌ IndexTTS 健康檢查失敗: {e}")
            return False
    
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """使用 IndexTTS VLLM API 生成音頻"""
        if not self.is_available or not self.session:
            print(f"⚠️ IndexTTS VLLM 引擎不可用，跳過音頻生成")
            return None
        
        try:
            # 獲取聲音配置
            voice_config = await self._get_voice_config(voice_id)
            if not voice_config:
                print(f"❌ IndexTTS VLLM: 找不到聲音配置 {voice_id}")
                return None
            
            print(f"🎵 使用IndexTTS VLLM: '{text}' (長度: {len(text)}) -> {voice_config['name']}")
            
            # 準備新版 API 請求數據
            payload = {
                "text": text,
                "audio_paths": voice_config["audio_paths"],
                "seed": voice_config.get("seed", 2)
            }
            
            # 調用新的 /tts_url 接口
            timeout = aiohttp.ClientTimeout(total=180)  # 3分鐘超時
            async with self.session.post(
                f"{self.api_base_url}/tts_url",
                json=payload,
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    # 獲取 WAV 音頻數據 (新版本已經自動轉換為16kHz)
                    audio_data = await response.read()
                    
                    # 編碼為 Base64
                    base64_string = base64.b64encode(audio_data).decode('utf-8')
                    print(f"✅ IndexTTS VLLM 生成成功: {len(audio_data)} bytes (已自動轉換為16kHz)")
                    return base64_string
                else:
                    error_text = await response.text()
                    print(f"❌ IndexTTS VLLM API 錯誤: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            print("❌ IndexTTS VLLM API 請求超時")
            return None
        except Exception as e:
            print(f"❌ IndexTTS VLLM 生成失敗: {e}")
            return None
    
    async def _get_voice_config(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """從新的 voices.json 配置獲取聲音配置"""
        try:
            # 讀取新的聲音配置文件
            config_path = "indextts-service/assets/voices.json"
            if not os.path.exists(config_path):
                print(f"❌ IndexTTS VLLM 配置文件不存在: {config_path}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                voices_config = json.load(f)
            
            # 查找匹配的聲音配置
            voices = voices_config.get("voices", [])
            for voice in voices:
                if voice.get("id") == voice_id:
                    return {
                        "id": voice_id,
                        "name": voice.get("name", voice_id),
                        "character": voice.get("character", voice_id.lower()),
                        "audio_paths": voice.get("audio_paths", []),
                        "seed": voice.get("seed", 2)
                    }
            
            # 如果沒找到，嘗試使用第一個可用聲音
            if voices:
                default_voice = voices[0]
                print(f"⚠️ 聲音 {voice_id} 不存在，使用默認聲音: {default_voice.get('id')}")
                return {
                    "id": default_voice.get("id"),
                    "name": default_voice.get("name"),
                    "character": default_voice.get("character"),
                    "audio_paths": default_voice.get("audio_paths", []),
                    "seed": default_voice.get("seed", 2)
                }
                        
        except Exception as e:
            print(f"❌ 獲取聲音配置失敗: {e}")
        
        return None
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取可用的聲音列表"""
        try:
            config_path = "indextts-service/assets/voices.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    voices_config = json.load(f)
                
                voices_dict = {}
                for voice in voices_config.get("voices", []):
                    voice_id = voice.get("id")
                    if voice_id:
                        voices_dict[voice_id] = {
                            "name": voice.get("name", voice_id),
                            "display_name": voice.get("name", voice_id),  # 添加 display_name 字段
                            "description": voice.get("description", ""),
                            "character": voice.get("character", voice_id.lower()),
                            "seed": voice.get("seed", 2),
                            "recommended": False  # 添加 recommended 字段
                        }
                return voices_dict
        except Exception as e:
            print(f"❌ 獲取聲音列表失敗: {e}")
        
        return {}
    
    def get_recommended_voices(self) -> list:
        """獲取推薦聲音列表"""
        voices = self.get_available_voices()
        return list(voices.keys())[:3]  # 返回前3個聲音作為推薦
    
    async def close(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
