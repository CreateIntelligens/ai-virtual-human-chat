"""
EdgeTTS 引擎實現
"""
import os
import base64
import tempfile
import subprocess
import asyncio
from typing import Optional, Dict, Any
from .base_tts import BaseTTSEngine


class EdgeTTSEngine(BaseTTSEngine):
    """EdgeTTS 引擎實現"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.voice_mapping = {}
        
    async def initialize(self) -> bool:
        """初始化 EdgeTTS 引擎"""
        try:
            import edge_tts
            self.is_available = True
            print("✅ EdgeTTS 引擎初始化成功")
            return True
        except ImportError:
            print("❌ EdgeTTS 套件未安裝")
            self.is_available = False
            return False
        except Exception as e:
            print(f"❌ EdgeTTS 初始化失敗: {e}")
            self.is_available = False
            return False
    
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """使用 EdgeTTS 生成音頻"""
        if not self.is_available:
            return None
            
        try:
            import edge_tts
            
            # 獲取實際的引擎聲音 ID
            engine_voice_id = self._get_engine_voice_id(voice_id)
            if not engine_voice_id:
                print(f"❌ 找不到聲音映射: {voice_id}")
                return None
            
            print(f"🎵 使用EdgeTTS: '{text}' (長度: {len(text)}) -> {engine_voice_id}")
            
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_filename = tmp_file.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as converted_file:
                converted_filename = converted_file.name
            
            try:
                # 生成 EdgeTTS 音頻
                communicate = edge_tts.Communicate(text, engine_voice_id)
                await communicate.save(tmp_filename)
                
                # 轉換為 16kHz 單聲道以匹配原始格式
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
                
                # 讀取音頻文件並轉換為 Base64
                with open(audio_filename, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                base64_string = base64.b64encode(audio_data).decode('utf-8')
                print(f"🔊 EdgeTTS 生成成功: {len(audio_data)} bytes")
                return base64_string
                
            finally:
                # 清理臨時文件
                try:
                    os.unlink(tmp_filename)
                    if os.path.exists(converted_filename):
                        os.unlink(converted_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ EdgeTTS 生成失敗: {e}")
            return None
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取可用的聲音列表"""
        return self.config.get("voices", {})
    
    def _get_engine_voice_id(self, voice_id: str) -> Optional[str]:
        """獲取引擎實際使用的聲音 ID"""
        voices = self.get_available_voices()
        
        # 1. 直接查找（原始 ID）
        voice_config = voices.get(voice_id)
        if voice_config:
            return voice_config.get("engine_voice_id")
        
        # 2. 查找帶前綴的 ID（為了兼容新的配置格式）
        prefixed_voice_id = f"edge_{voice_id}"
        voice_config = voices.get(prefixed_voice_id)
        if voice_config:
            return voice_config.get("engine_voice_id")
        
        # 3. 如果都找不到，檢查是否 voice_id 本身就是 engine_voice_id
        for config in voices.values():
            if config.get("engine_voice_id") == voice_id:
                return voice_id
        
        return None
