"""
TTS 配置管理器 - 統一配置讀取版本
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class TTSConfigManager:
    """TTS 配置管理器 - 直接讀取各服務的原始配置"""
    
    def __init__(self, config_dir: str = "web_demo/voiceapi/tts_configs"):
        self.config_dir = Path(config_dir)
        self.configs = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """載入所有 TTS 配置"""
        try:
            # 載入 EdgeTTS 靜態配置
            self._load_edge_tts_config()
            
            # 載入 CosyVoice 服務配置
            self._load_cosyvoice_config()
            
            # 載入 IndexTTS 服務配置
            self._load_indextts_config()
            
            print(f"✅ 載入了 {len(self.configs)} 個 TTS 配置")
            
        except Exception as e:
            print(f"❌ 載入 TTS 配置失敗: {e}")
    
    def _load_edge_tts_config(self):
        """載入 EdgeTTS 靜態配置"""
        try:
            edge_config_path = self.config_dir / "edge_tts.json"
            if edge_config_path.exists():
                with open(edge_config_path, 'r', encoding='utf-8') as f:
                    edge_raw = json.load(f)
                
                # 轉換為標準格式（添加前綴）
                self.configs["edge_tts"] = self._convert_edge_tts_format(edge_raw)
                print(f"✅ 載入 EdgeTTS 配置")
            else:
                print(f"⚠️ EdgeTTS 配置文件不存在: {edge_config_path}")
        except Exception as e:
            print(f"❌ 載入 EdgeTTS 配置失敗: {e}")
    
    def _load_cosyvoice_config(self):
        """載入 CosyVoice 服務配置"""
        try:
            cosyvoice_config_path = "cosyvoice-service/config/voices.local.json"
            if os.path.exists(cosyvoice_config_path):
                with open(cosyvoice_config_path, 'r', encoding='utf-8') as f:
                    cosyvoice_raw = json.load(f)
                
                # 轉換為標準格式
                self.configs["cosyvoice"] = self._convert_cosyvoice_format(cosyvoice_raw)
                print(f"✅ 載入 CosyVoice 配置")
            else:
                print(f"⚠️ CosyVoice 配置文件不存在: {cosyvoice_config_path}")
        except Exception as e:
            print(f"❌ 載入 CosyVoice 配置失敗: {e}")
    
    def _load_indextts_config(self):
        """載入 IndexTTS 服務配置"""
        try:
            indextts_config_path = "indextts-service/config/voices.json"
            if os.path.exists(indextts_config_path):
                with open(indextts_config_path, 'r', encoding='utf-8') as f:
                    indextts_raw = json.load(f)
                
                # 轉換為標準格式
                self.configs["indextts"] = self._convert_indextts_format(indextts_raw)
                print(f"✅ 載入 IndexTTS 配置")
            else:
                print(f"⚠️ IndexTTS 配置文件不存在: {indextts_config_path}")
        except Exception as e:
            print(f"❌ 載入 IndexTTS 配置失敗: {e}")
    
    def _convert_edge_tts_format(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """將 EdgeTTS 原始配置轉換為標準格式"""
        voices = {}
        recommended = []
        
        for voice_id, voice_config in raw_config.get("voices", {}).items():
            # 自動添加引擎前綴
            prefixed_id = f"edge_{voice_id}"
            voices[prefixed_id] = {
                "engine_voice_id": voice_config.get("engine_voice_id", voice_id),  # 使用配置中的 engine_voice_id
                "display_name": voice_config.get("display_name", voice_id),
                "description": voice_config.get("description", ""),
                "gender": voice_config.get("gender", "unknown"),
                "age_group": voice_config.get("age_group", "adult"),
                "language": voice_config.get("language", "zh-CN"),
                "quality": voice_config.get("quality", "high"),
                "recommended": voice_config.get("recommended", False),
                "tags": voice_config.get("tags", [])
            }
            if voice_config.get("recommended", False):
                recommended.append(prefixed_id)
        
        return {
            "provider_info": {
                "provider": "edge_tts",
                "display_name": raw_config.get("display_name", "EdgeTTS"),
                "description": raw_config.get("description", "微軟高品質神經網路語音合成"),
                "requires_internet": raw_config.get("requires_internet", True),
                "supported_languages": raw_config.get("supported_languages", ["zh-CN", "zh-TW", "en-US"]),
                "voices": voices,
                "default_voice": f"edge_{raw_config.get('default_voice', '')}" if raw_config.get('default_voice') else "",
                "fallback_voice": f"edge_{raw_config.get('fallback_voice', '')}" if raw_config.get('fallback_voice') else "",
                "audio_settings": raw_config.get("audio_settings", {
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "bit_depth": 16
                })
            },
            "voices": voices,
            "recommended": recommended
        }
    
    def _convert_cosyvoice_format(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """將 CosyVoice 原始配置轉換為標準格式"""
        voices = {}
        recommended = []
        
        for voice in raw_config.get("voices", []):
            voice_id = voice.get("id")
            if voice_id:
                # 自動添加引擎前綴
                prefixed_id = f"cosyvoice_{voice_id}"
                voices[prefixed_id] = {
                    "engine_voice_id": voice_id,  # 保留原始 ID 給引擎使用
                    "display_name": voice.get("name", voice_id),
                    "description": voice.get("description", ""),
                    "gender": "female" if "女" in voice.get("name", "") else "male",
                    "age_group": "adult",
                    "language": "zh-CN",
                    "quality": "high",
                    "recommended": True,
                    "tags": ["professional", "clear"]
                }
                recommended.append(prefixed_id)
        
        return {
            "provider_info": {
                "provider": "cosyvoice",
                "display_name": "CosyVoice",
                "description": "阿里巴巴高品質語音合成引擎",
                "requires_internet": True,
                "supported_languages": ["zh-CN", "zh-TW", "en-US"],
                "voices": voices,
                "default_voice": recommended[0] if recommended else "",
                "fallback_voice": recommended[0] if recommended else "",
                "api_config": {
                    "base_url": "http://cosyvoice-service:50001",
                    "timeout": None,
                    "retry_attempts": 3,
                    "health_check_interval": 60
                },
                "audio_settings": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "bit_depth": 16
                }
            },
            "voices": voices,
            "recommended": recommended
        }
    
    def _convert_indextts_format(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """將 IndexTTS 原始配置轉換為標準格式"""
        voices = {}
        recommended = []
        
        for voice in raw_config.get("voices", []):
            voice_id = voice.get("id")
            if voice_id:
                # 自動添加引擎前綴
                prefixed_id = f"indextts_{voice_id}"
                voices[prefixed_id] = {
                    "engine_voice_id": voice_id,  # 保留原始 ID 給引擎使用
                    "display_name": voice.get("name", voice_id),
                    "description": voice.get("description", ""),
                    "gender": "female" if voice_id == "Aikka" else "male",
                    "age_group": "adult",
                    "language": "zh-CN",
                    "quality": "high",
                    "recommended": True,
                    "tags": ["custom", "clone"]
                }
                recommended.append(prefixed_id)
        
        return {
            "provider_info": {
                "provider": "indextts",
                "display_name": "IndexTTS",
                "description": "高品質語音克隆引擎，支援自定義聲音",
                "requires_internet": True,
                "supported_languages": ["zh-CN", "zh-TW", "en-US"],
                "voices": voices,
                "default_voice": recommended[0] if recommended else "",
                "fallback_voice": recommended[0] if recommended else "",
                "api_config": {
                    "base_url": "http://indextts-service:6008",
                    "timeout": 180,
                    "retry_attempts": 3,
                    "health_check_interval": 60
                },
                "audio_settings": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "wav",
                    "bit_depth": 16
                }
            },
            "voices": voices,
            "recommended": recommended
        }
    
    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """獲取指定提供商的配置"""
        return self.configs.get(provider)
    
    def get_voice_config(self, provider: str, voice_id: str) -> Optional[Dict[str, Any]]:
        """獲取指定聲音的配置"""
        config = self.get_provider_config(provider)
        if not config:
            return None
        return config.get("voices", {}).get(voice_id)
    
    def get_engine_voice_id(self, provider: str, voice_id: str) -> Optional[str]:
        """獲取引擎實際使用的聲音 ID"""
        voice_config = self.get_voice_config(provider, voice_id)
        if not voice_config:
            return None
        return voice_config.get("engine_voice_id")
    
    def get_available_voices(self, provider: str) -> Dict[str, Dict[str, Any]]:
        """獲取指定提供商的可用聲音"""
        config = self.get_provider_config(provider)
        if not config:
            return {}
        return config.get("voices", {})
    
    def get_recommended_voices(self, provider: str) -> List[str]:
        """獲取推薦的聲音列表"""
        config = self.get_provider_config(provider)
        if not config:
            return []
        return config.get("recommended", [])
    
    def get_available_providers(self) -> List[str]:
        """獲取所有可用的提供商列表"""
        return list(self.configs.keys())
    
    def should_use_primary_engine(self, voice_id: str, requested_provider: str = None) -> tuple[str, str]:
        """
        智能引擎選擇邏輯 - 支持前綴解析和自動引擎選擇
        返回 (實際使用的引擎, 實際使用的聲音ID)
        """
        # 1. 如果用戶明確指定了引擎，直接使用
        if requested_provider:
            # 如果是帶前綴的聲音 ID，需要解析出原始 ID
            actual_voice_id = self._extract_original_voice_id(voice_id, requested_provider)
            return requested_provider, actual_voice_id
        
        # 2. 解析前綴自動選擇引擎
        if voice_id.startswith('edge_'):
            return 'edge_tts', voice_id[5:]  # 移除 'edge_' 前綴
        elif voice_id.startswith('cosyvoice_'):
            return 'cosyvoice', voice_id[10:]  # 移除 'cosyvoice_' 前綴
        elif voice_id.startswith('indextts_'):
            return 'indextts', voice_id[9:]  # 移除 'indextts_' 前綴
        
        # 3. 動態查找聲音所屬的引擎
        for provider in self.configs.keys():
            voices = self.get_available_voices(provider)
            if voice_id in voices:
                actual_voice_id = self._extract_original_voice_id(voice_id, provider)
                return provider, actual_voice_id
        
        # 4. 如果都找不到，使用默認引擎
        return "edge_tts", voice_id
    
    def _extract_original_voice_id(self, voice_id: str, provider: str) -> str:
        """從帶前綴的聲音 ID 中提取原始 ID"""
        voice_config = self.get_voice_config(provider, voice_id)
        if voice_config and 'engine_voice_id' in voice_config:
            return voice_config['engine_voice_id']
        return voice_id
    
    def get_default_voice(self, provider: str) -> str:
        """獲取指定提供商的默認聲音"""
        config = self.get_provider_config(provider)
        if not config:
            return ""
        provider_info = config.get("provider_info", {})
        return provider_info.get("default_voice", "")
    
    def reload_configs(self):
        """重新載入配置（用於熱更新）"""
        self.configs.clear()
        self.load_all_configs()
