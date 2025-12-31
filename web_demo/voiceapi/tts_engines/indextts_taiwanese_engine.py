"""
IndexTTS 台語引擎實現 - 固定使用 gentle_female 角色和 seed=2
API: http://10.9.0.35:8011/tts
"""
import os
import base64
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from .base_tts import BaseTTSEngine


class IndexTTSTaiwaneseEngine(BaseTTSEngine):
    """IndexTTS 台語引擎實現 - 通過固定 API 調用"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base_url = None
        self.session = None
        # 固定參數
        self.character = "gentle_female"
        self.seed = 2
        
    async def initialize(self) -> bool:
        """初始化 IndexTTS 台語引擎"""
        try:
            # 從配置文件獲取 API 地址
            provider_info = self.config.get('provider_info', {})
            api_config = provider_info.get('api_config', {})
            self.api_base_url = api_config.get('base_url', 'http://10.9.0.35:8011')
            
            # 也支援環境變數覆蓋
            self.api_base_url = os.getenv('INDEXTTS_TAIWANESE_API_URL', self.api_base_url)
            
            print(f"🔧 IndexTTS 台語 API URL: {self.api_base_url}")
            
            # 創建 HTTP 會話
            self.session = aiohttp.ClientSession()
            
            # 測試 API 連接（使用 /audio/voices 端點）
            health_check = await self._check_api_health()
            if health_check:
                self.is_available = True
                print(f"✅ IndexTTS 台語 API 連接成功: {self.api_base_url}")
                return True
            else:
                # API 無法連接，不啟用此引擎（前端不會顯示）
                print(f"❌ IndexTTS 台語 API 無法連接: {self.api_base_url}，引擎不啟用")
                self.is_available = False
                await self.close()
                return False
                
        except Exception as e:
            print(f"❌ IndexTTS 台語初始化失敗: {e}")
            return False
    
    async def _check_api_health(self) -> bool:
        """檢查 IndexTTS 台語 API 健康狀態（使用 /audio/voices 端點）"""
        try:
            # 使用 /audio/voices 端點來檢查 API 是否可用
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.get(f"{self.api_base_url}/audio/voices", timeout=timeout) as response:
                if response.status == 200:
                    print(f"✅ IndexTTS 台語 /audio/voices 健康檢查成功")
                    return True
                else:
                    print(f"❌ IndexTTS 台語 /audio/voices 返回狀態碼: {response.status}")
                    return False
        except aiohttp.ClientConnectorError as e:
            print(f"❌ IndexTTS 台語無法連接到伺服器: {e}")
            return False
        except asyncio.TimeoutError:
            print(f"❌ IndexTTS 台語健康檢查超時")
            return False
        except Exception as e:
            print(f"❌ IndexTTS 台語健康檢查失敗: {e}")
            return False
    
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """使用 IndexTTS 台語 API 生成音頻"""
        if not self.is_available or not self.session:
            print(f"⚠️ IndexTTS 台語引擎不可用，跳過音頻生成")
            return None
        
        try:
            print(f"🎵 使用 IndexTTS 台語: '{text}' (長度: {len(text)}) -> character={self.character}, seed={self.seed}")
            
            # 準備 API 請求數據（固定使用 gentle_female 和 seed=2）
            payload = {
                "text": text,
                "character": self.character,
                "seed": self.seed
            }
            
            # 調用 /tts 接口
            timeout = aiohttp.ClientTimeout(total=180)  # 3分鐘超時
            async with self.session.post(
                f"{self.api_base_url}/tts",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    # 獲取音頻數據
                    audio_data = await response.read()
                    
                    # 編碼為 Base64
                    base64_string = base64.b64encode(audio_data).decode('utf-8')
                    
                    print(f"✅ IndexTTS 台語生成成功，音頻大小: {len(audio_data)} bytes")
                    return base64_string
                else:
                    error_text = await response.text()
                    print(f"❌ IndexTTS 台語 API 返回錯誤 {response.status}: {error_text}")
                    return None
                    
        except aiohttp.ClientError as e:
            print(f"❌ IndexTTS 台語網絡錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ IndexTTS 台語生成失敗: {e}")
            return None
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取可用的聲音列表"""
        # 從配置中獲取聲音列表
        provider_info = self.config.get("provider_info", {})
        return provider_info.get("voices", {})
    
    async def close(self):
        """關閉引擎，清理資源"""
        if self.session:
            await self.session.close()
            self.session = None
