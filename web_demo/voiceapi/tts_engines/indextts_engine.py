"""
IndexTTS 引擎實現 - 基於 IndexTTS API 調用方式
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
    """IndexTTS 引擎實現 - 通過 API 調用"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base_url = None
        self.session = None
        
    async def initialize(self) -> bool:
        """初始化 IndexTTS 引擎"""
        try:
            # 從配置文件獲取 API 地址
            api_config = self.config.get('api_config', {})
            self.api_base_url = api_config.get('base_url', 'http://indextts-service:6008')
            
            # 也支援環境變數覆蓋
            self.api_base_url = os.getenv('INDEXTTS_API_URL', self.api_base_url)
            
            # 創建 HTTP 會話
            self.session = aiohttp.ClientSession()
            
            # 測試 API 連接
            health_check = await self._check_api_health()
            if health_check:
                self.is_available = True
                print(f"✅ IndexTTS API 連接成功: {self.api_base_url}")
                return True
            else:
                print(f"❌ IndexTTS API 無法連接: {self.api_base_url}")
                return False
                
        except Exception as e:
            print(f"❌ IndexTTS 初始化失敗: {e}")
            return False
    
    async def _check_api_health(self) -> bool:
        """檢查 IndexTTS API 健康狀態"""
        try:
            # 嘗試訪問 API 文檔頁面來測試連接
            async with self.session.get(f"{self.api_base_url}/docs", timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """使用 IndexTTS API 生成音頻"""
        if not self.is_available or not self.session:
            print(f"⚠️ IndexTTS 引擎不可用，跳過音頻生成")
            return None
        
        try:
            # 獲取聲音配置
            voice_config = await self._get_voice_config(voice_id)
            if not voice_config:
                print(f"❌ IndexTTS: 找不到聲音配置 {voice_id}")
                return None
            
            print(f"🎵 使用IndexTTS: '{text}' (長度: {len(text)}) -> {voice_config['name']}")
            
            # 獲取參考音頻文件路徑
            audio_file_path = await self._get_audio_file_path(voice_config['audio_file'])
            if not audio_file_path:
                print(f"❌ IndexTTS: 找不到參考音頻文件 {voice_config['audio_file']}")
                print(f"💡 提示: 請將參考音頻文件放置在 indextts-service/config/audio_samples/ 目錄下")
                return None
            
            # 準備 API 請求數據
            form_data = aiohttp.FormData()
            
            # 讀取參考音頻文件內容到內存中，避免文件關閉問題
            with open(audio_file_path, 'rb') as f:
                audio_content = f.read()
            
            # 使用 BytesIO 創建文件對象
            audio_stream = BytesIO(audio_content)
            form_data.add_field('prompt_audio', audio_stream, filename=voice_config['audio_file'])
            
            # 添加文本和參數
            form_data.add_field('text', text)
            
            # 添加 IndexTTS 特定參數
            parameters = voice_config.get('parameters', {})
            for key, value in parameters.items():
                form_data.add_field(key, str(value))
            
            # 調用 IndexTTS API
            timeout = aiohttp.ClientTimeout(total=180)  # 3分鐘超時
            async with self.session.post(
                f"{self.api_base_url}/tts",
                data=form_data,
                timeout=timeout
            ) as response:
                
                if response.status == 200:
                    # 獲取 WAV 音頻數據
                    audio_data = await response.read()
                    
                    # 使用高品質重採樣為 16kHz 以匹配 DH_Live 要求
                    resampled_audio = await self._resample_audio_hq(audio_data)
                    if resampled_audio:
                        # 編碼為 Base64
                        base64_string = base64.b64encode(resampled_audio).decode('utf-8')
                        print(f"✅ IndexTTS 生成成功: {len(audio_data)} bytes -> {len(resampled_audio)} bytes (高品質重採樣為16kHz)")
                        return base64_string
                    else:
                        # 重採樣失敗，使用原始重採樣方法
                        resampled_audio = await self._resample_audio(audio_data)
                        if resampled_audio:
                            base64_string = base64.b64encode(resampled_audio).decode('utf-8')
                            print(f"⚠️ 使用標準重採樣: {len(audio_data)} bytes -> {len(resampled_audio)} bytes (16kHz)")
                            return base64_string
                        else:
                            # 完全失敗，使用原始音頻
                            base64_string = base64.b64encode(audio_data).decode('utf-8')
                            print(f"⚠️ 重採樣失敗，使用原始音頻: {len(audio_data)} bytes")
                            return base64_string
                else:
                    error_text = await response.text()
                    print(f"❌ IndexTTS API 錯誤: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            print("❌ IndexTTS API 請求超時")
            return None
        except Exception as e:
            print(f"❌ IndexTTS 生成失敗: {e}")
            return None
    
    async def _get_voice_config(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """直接從 IndexTTS 服務配置獲取聲音配置"""
        try:
            # 直接讀取 IndexTTS 服務配置文件
            config_path = "indextts-service/config/voices.json"
            if not os.path.exists(config_path):
                print(f"❌ IndexTTS 配置文件不存在: {config_path}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                indextts_config = json.load(f)
            
            # 查找匹配的聲音配置
            voices = indextts_config.get("voices", [])
            for voice in voices:
                if voice.get("id") == voice_id:
                    return {
                        "id": voice_id,
                        "name": voice.get("name", voice_id),
                        "audio_file": voice.get("audio_file"),
                        "parameters": voice.get("parameters", {})
                    }
            
            # 如果沒找到，嘗試使用第一個可用聲音
            if voices:
                default_voice = voices[0]
                print(f"⚠️ 聲音 {voice_id} 不存在，使用默認聲音: {default_voice.get('id')}")
                return {
                    "id": default_voice.get("id"),
                    "name": default_voice.get("name"),
                    "audio_file": default_voice.get("audio_file"),
                    "parameters": default_voice.get("parameters", {})
                }
                        
        except Exception as e:
            print(f"❌ 獲取聲音配置失敗: {e}")
        
        return None
    
    async def _get_audio_file_path(self, audio_file: str) -> Optional[str]:
        """獲取參考音頻文件的完整路徑 - 統一使用 indextts-service 目錄"""
        try:
            # 只使用統一路徑
            audio_path = f"indextts-service/config/audio_samples/{audio_file}"
            
            if os.path.exists(audio_path):
                print(f"✅ 找到音頻文件: {audio_path}")
                return audio_path
            
            print(f"❌ 音頻文件不存在: {audio_path}")
            print(f"💡 請將參考音頻文件放置在: indextts-service/config/audio_samples/")
            return None
            
        except Exception as e:
            print(f"❌ 獲取音頻文件路徑失敗: {e}")
            return None
    
    async def _convert_to_mono(self, audio_data: bytes) -> Optional[bytes]:
        """將音頻轉換為單聲道，保持原始採樣率"""
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as input_file:
                input_filename = input_file.name
                input_file.write(audio_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as output_file:
                output_filename = output_file.name
            
            try:
                # 使用 FFmpeg 轉換為單聲道，保持原始採樣率
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', input_filename,
                    '-ac', '1',      # 單聲道
                    '-sample_fmt', 's16',  # 16位PCM
                    output_filename
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ FFmpeg 單聲道轉換失敗: {result.stderr}")
                    return None
                
                # 讀取轉換後的音頻數據
                with open(output_filename, "rb") as f:
                    converted_data = f.read()
                
                return converted_data
                
            finally:
                # 清理臨時文件
                try:
                    os.unlink(input_filename)
                    os.unlink(output_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ 單聲道轉換過程失敗: {e}")
            return None
    
    async def _resample_audio_hq(self, audio_data: bytes) -> Optional[bytes]:
        """使用高品質重採樣器將音頻重採樣為 16kHz"""
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as input_file:
                input_filename = input_file.name
                input_file.write(audio_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as output_file:
                output_filename = output_file.name
            
            try:
                # 使用 FFmpeg 高品質重採樣 (soxr)
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', input_filename,
                    '-ar', '16000',  # 目標採樣率 16kHz
                    '-ac', '1',      # 單聲道
                    '-sample_fmt', 's16',  # 16位PCM
                    '-af', 'aresample=resampler=soxr:precision=28:cheby=1',  # 高品質重採樣
                    output_filename
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ FFmpeg 高品質重採樣失敗: {result.stderr}")
                    return None
                
                # 讀取重採樣後的音頻數據
                with open(output_filename, "rb") as f:
                    resampled_data = f.read()
                
                return resampled_data
                
            finally:
                # 清理臨時文件
                try:
                    os.unlink(input_filename)
                    os.unlink(output_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ 高品質重採樣過程失敗: {e}")
            return None
    
    async def _resample_audio(self, audio_data: bytes) -> Optional[bytes]:
        """將音頻重採樣為 16kHz"""
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as input_file:
                input_filename = input_file.name
                input_file.write(audio_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as output_file:
                output_filename = output_file.name
            
            try:
                # 使用 FFmpeg 重採樣
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', input_filename,
                    '-ar', '16000',  # 目標採樣率 16kHz
                    '-ac', '1',      # 單聲道
                    '-sample_fmt', 's16',  # 16位PCM
                    output_filename
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ FFmpeg 重採樣失敗: {result.stderr}")
                    return None
                
                # 讀取重採樣後的音頻數據
                with open(output_filename, "rb") as f:
                    resampled_data = f.read()
                
                return resampled_data
                
            finally:
                # 清理臨時文件
                try:
                    os.unlink(input_filename)
                    os.unlink(output_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ 重採樣過程失敗: {e}")
            return None
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取可用的聲音列表"""
        return self.config.get("voices", {})
    
    async def close(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
