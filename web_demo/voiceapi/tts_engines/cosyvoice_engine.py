"""
CosyVoice 引擎實現 - 基於 ai-voice-studio 的 API 調用方式
"""
import os
import base64
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from .base_tts import BaseTTSEngine


class CosyVoiceEngine(BaseTTSEngine):
    """CosyVoice 引擎實現 - 通過 API 調用"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base_url = None
        self.session = None
        
    async def initialize(self) -> bool:
        """初始化 CosyVoice 引擎"""
        try:
            # 從配置文件獲取 API 地址
            api_config = self.config.get('api_config', {})
            self.api_base_url = api_config.get('base_url', 'http://cosyvoice-service:50001')
            
            # 也支援環境變數覆蓋
            self.api_base_url = os.getenv('COSYVOICE_API_URL', self.api_base_url)
            
            # 創建 HTTP 會話
            self.session = aiohttp.ClientSession()
            
            # 測試 API 連接
            health_check = await self._check_api_health()
            if health_check:
                self.is_available = True
                print(f"✅ CosyVoice API 連接成功: {self.api_base_url}")
                return True
            else:
                print(f"❌ CosyVoice API 無法連接: {self.api_base_url}")
                return False
                
        except Exception as e:
            print(f"❌ CosyVoice 初始化失敗: {e}")
            return False
    
    async def _check_api_health(self) -> bool:
        """檢查 CosyVoice API 健康狀態"""
        try:
            # 嘗試獲取聲音列表來測試連接
            async with self.session.get(f"{self.api_base_url}/voices", timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """使用 CosyVoice API 生成音頻"""
        if not self.is_available or not self.session:
            return None
        
        try:
            # 獲取聲音配置
            voice_config = await self._get_voice_config(voice_id)
            if not voice_config:
                print(f"❌ 找不到聲音配置: {voice_id}")
                return None
            
            print(f"🎵 使用CosyVoice: '{text}' (長度: {len(text)}) -> {voice_config['name']}")
            
            # 準備 API 請求數據 - 使用 ai-voice-studio 的格式
            form_data = aiohttp.FormData()
            form_data.add_field('tts_text', text)
            form_data.add_field('voice_id', voice_id)
            
            # 調用 CosyVoice API - 使用預配置聲音端點
            # 移除超時限制，因為 CosyVoice 在 CPU 模式下可能需要很長時間
            timeout = aiohttp.ClientTimeout(total=None)  # 無超時限制
            async with self.session.post(
                f"{self.api_base_url}/inference_with_voice_config",
                data=form_data,
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    # 獲取 WAV 音頻數據
                    audio_data = await response.read()
                    
                    # 編碼為 Base64
                    base64_string = base64.b64encode(audio_data).decode('utf-8')
                    
                    print(f"✅ CosyVoice 生成成功: {len(audio_data)} bytes")
                    return base64_string
                else:
                    error_text = await response.text()
                    print(f"❌ CosyVoice API 錯誤: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            print("❌ CosyVoice API 請求超時")
            return None
        except Exception as e:
            print(f"❌ CosyVoice 生成失敗: {e}")
            return None
    
    async def _get_voice_config(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """從 CosyVoice API 獲取聲音配置"""
        try:
            async with self.session.get(f"{self.api_base_url}/voices", timeout=5) as response:
                if response.status == 200:
                    voices_data = await response.json()
                    voices = voices_data.get('voices', [])
                    
                    # 查找匹配的聲音配置
                    for voice in voices:
                        if voice.get('id') == voice_id:
                            return voice
                    
                    # 如果沒找到，返回第一個可用聲音
                    if voices:
                        print(f"⚠️ 聲音 {voice_id} 不存在，使用默認聲音: {voices[0]['id']}")
                        return voices[0]
                        
        except Exception as e:
            print(f"❌ 獲取聲音配置失敗: {e}")
        
        return None
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取可用的聲音列表"""
        return self.config.get("voices", {})
    
    async def close(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
