"""
TTS 配置管理器
"""
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class TTSConfigManager:
    """TTS 配置管理器"""
    
    def __init__(self, config_dir: str = "web_demo/voiceapi/tts_configs"):
        self.config_dir = Path(config_dir)
        self.configs = {}
        self.voice_mapping = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """載入所有 TTS 配置"""
        try:
            # 載入各個 TTS 引擎配置
            for config_file in self.config_dir.glob("*.json"):
                if config_file.name != "voice_mapping.json":
                    provider = config_file.stem
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.configs[provider] = json.load(f)
            
            # 載入通用聲音映射
            mapping_file = self.config_dir / "voice_mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.voice_mapping = json.load(f)
            
            print(f"✅ 載入了 {len(self.configs)} 個 TTS 配置")
            
        except Exception as e:
            print(f"❌ 載入 TTS 配置失敗: {e}")
    
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
        voices = self.get_available_voices(provider)
        return [
            voice_id for voice_id, voice_config in voices.items()
            if voice_config.get("recommended", False)
        ]
    
    def get_available_providers(self) -> List[str]:
        """獲取所有可用的提供商列表"""
        return list(self.configs.keys())
    
    def map_universal_voice(self, universal_id: str, target_provider: str) -> Optional[str]:
        """將通用聲音 ID 映射到目標提供商"""
        universal_voices = self.voice_mapping.get("universal_voices", {})
        universal_config = universal_voices.get(universal_id)
        if not universal_config:
            return None
        
        mappings = universal_config.get("mappings", {})
        return mappings.get(target_provider)
    
    def get_voice_primary_engine(self, voice_id: str) -> Optional[str]:
        """獲取聲音的主要引擎"""
        direct_mappings = self.voice_mapping.get("direct_voice_mappings", {})
        voice_config = direct_mappings.get(voice_id)
        if voice_config:
            return voice_config.get("primary_engine")
        return None
    
    def get_voice_fallback_mapping(self, voice_id: str, target_provider: str) -> Optional[str]:
        """獲取聲音在目標引擎中的降級映射"""
        direct_mappings = self.voice_mapping.get("direct_voice_mappings", {})
        voice_config = direct_mappings.get(voice_id)
        if voice_config:
            fallback_mappings = voice_config.get("fallback_mappings", {})
            return fallback_mappings.get(target_provider)
        return None
    
    def should_use_primary_engine(self, voice_id: str, requested_provider: str = None) -> tuple[str, str]:
        """
        判斷是否應該使用主要引擎
        返回 (實際使用的引擎, 實際使用的聲音ID)
        """
        # 檢查是否有直接聲音映射
        primary_engine = self.get_voice_primary_engine(voice_id)
        
        if primary_engine:
            # 如果用戶指定了引擎且與主要引擎一致，直接使用
            if requested_provider == primary_engine:
                return primary_engine, voice_id
            
            # 如果用戶沒有指定引擎，使用主要引擎
            if not requested_provider:
                return primary_engine, voice_id
            
            # 如果用戶指定了不同的引擎，嘗試映射
            fallback_voice = self.get_voice_fallback_mapping(voice_id, requested_provider)
            if fallback_voice:
                return requested_provider, fallback_voice
            
            # 如果映射失敗，回到主要引擎
            return primary_engine, voice_id
        
        # 沒有直接映射，使用請求的引擎或默認引擎
        return requested_provider or "edge_tts", voice_id
    
    def get_default_voice(self, provider: str) -> str:
        """獲取指定提供商的默認聲音"""
        config = self.get_provider_config(provider)
        if not config:
            return ""
        return config.get("default_voice", "")
    
    def reload_configs(self):
        """重新載入配置（用於熱更新）"""
        self.configs.clear()
        self.voice_mapping.clear()
        self.load_all_configs()
