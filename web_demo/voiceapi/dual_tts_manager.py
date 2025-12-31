"""
EdgeTTS + CosyVoice + IndexTTS + IndexTTS台語 四引擎管理器
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from .tts_config_manager import TTSConfigManager
from .tts_engines.edge_tts_engine import EdgeTTSEngine
from .tts_engines.cosyvoice_engine import CosyVoiceEngine
from .tts_engines.indextts_engine import IndexTTSEngine
from .tts_engines.indextts_taiwanese_engine import IndexTTSTaiwaneseEngine


class DualTTSManager:
    """EdgeTTS + CosyVoice + IndexTTS + IndexTTS台語 四引擎管理器"""
    
    def __init__(self):
        self.engines = {}
        self.config_manager = TTSConfigManager()
        self.default_provider = os.getenv('TTS_DEFAULT_PROVIDER', 'edge_tts')
        
    async def initialize(self):
        """初始化所有引擎"""
        await self.initialize_engines()
        
    async def initialize_engines(self):
        """初始化 EdgeTTS、CosyVoice、IndexTTS 和 IndexTTS台語 引擎"""
        enabled_providers = os.getenv('TTS_ENABLED_PROVIDERS', 'edge_tts,cosyvoice,indextts,indextts_taiwanese').split(',')
        
        for provider in enabled_providers:
            provider = provider.strip()
            try:
                if provider == 'edge_tts' and os.getenv('EDGE_TTS_ENABLED', 'true').lower() == 'true':
                    config = self.config_manager.get_provider_config('edge_tts')
                    if config:
                        engine = EdgeTTSEngine(config)
                        if await engine.initialize():
                            self.engines[provider] = engine
                            print(f"✅ EdgeTTS 引擎已啟用")
                        else:
                            print(f"⚠️ EdgeTTS 引擎初始化失敗")
                    else:
                        print(f"⚠️ EdgeTTS 配置文件未找到")
                
                elif provider == 'cosyvoice' and os.getenv('COSYVOICE_ENABLED', 'true').lower() == 'true':
                    config = self.config_manager.get_provider_config('cosyvoice')
                    if config:
                        engine = CosyVoiceEngine(config)
                        if await engine.initialize():
                            self.engines[provider] = engine
                            print(f"✅ CosyVoice 引擎已啟用")
                        else:
                            print(f"⚠️ CosyVoice 引擎初始化失敗")
                    else:
                        print(f"⚠️ CosyVoice 配置文件未找到")
                
                elif provider == 'indextts' and os.getenv('INDEXTTS_ENABLED', 'true').lower() == 'true':
                    config = self.config_manager.get_provider_config('indextts')
                    if config:
                        engine = IndexTTSEngine(config)
                        if await engine.initialize():
                            self.engines[provider] = engine
                            print(f"✅ IndexTTS 引擎已啟用")
                        else:
                            print(f"⚠️ IndexTTS 引擎初始化失敗（可能是服務未啟動）")
                    else:
                        print(f"⚠️ IndexTTS 配置文件未找到")
                
                elif provider == 'indextts_taiwanese' and os.getenv('INDEXTTS_TAIWANESE_ENABLED', 'true').lower() == 'true':
                    config = self.config_manager.get_provider_config('indextts_taiwanese')
                    if config:
                        engine = IndexTTSTaiwaneseEngine(config)
                        if await engine.initialize():
                            self.engines[provider] = engine
                            print(f"✅ IndexTTS台語 引擎已啟用")
                        else:
                            print(f"⚠️ IndexTTS台語 引擎初始化失敗（可能是服務未啟動）")
                    else:
                        print(f"⚠️ IndexTTS台語 配置文件未找到")
                        
            except Exception as e:
                print(f"❌ {provider} 引擎初始化失敗: {e}")
                # 繼續初始化其他引擎，不讓單個引擎的錯誤影響整個系統
                continue
        
        print(f"🎯 TTS 引擎初始化完成，共啟用 {len(self.engines)} 個引擎: {list(self.engines.keys())}")
    
    async def generate_audio(self, text: str, provider: str = None, voice_id: str = "female-tianmei", **kwargs) -> Optional[str]:
        """生成音頻，嚴格按照指定引擎執行，不進行降級"""
        
        # 使用智能引擎選擇邏輯
        actual_provider, actual_voice_id = self.config_manager.should_use_primary_engine(voice_id, provider)
        
        print(f"🎯 嚴格引擎選擇: 請求引擎={provider}, 聲音={voice_id}")
        print(f"🤖 實際使用: 引擎={actual_provider}, 聲音={actual_voice_id}")
        
        # 檢查指定引擎是否可用
        engine = self.engines.get(actual_provider)
        if not engine:
            error_msg = f"❌ {actual_provider} 引擎未安裝或未啟用"
            print(error_msg)
            raise Exception(error_msg)
        
        if not engine.is_available:
            error_msg = f"❌ {actual_provider} 引擎不可用，請檢查引擎狀態"
            print(error_msg)
            raise Exception(error_msg)
        
        # 嘗試使用指定引擎生成音頻
        try:
            result = await engine.generate_audio(text, actual_voice_id, **kwargs)
            if result:
                print(f"✅ {actual_provider} 引擎生成成功")
                return result
            else:
                error_msg = f"❌ {actual_provider} 引擎生成音頻失敗，返回空結果"
                print(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"❌ {actual_provider} 引擎生成失敗: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """獲取可用的 TTS 引擎列表"""
        providers = []
        for provider, engine in self.engines.items():
            config = self.config_manager.get_provider_config(provider)
            providers.append({
                "id": provider,
                "name": config.get("display_name", provider),
                "description": config.get("description", ""),
                "status": "available" if engine.is_available else "unavailable",
                "requires_internet": config.get("requires_internet", False)
            })
        return providers
    
    def get_all_voices(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有引擎的聲音列表"""
        all_voices = {}
        for provider, engine in self.engines.items():
            try:
                if engine.is_available:
                    voices = engine.get_available_voices()
                    provider_config = self.config_manager.get_provider_config(provider)
                    all_voices[provider] = {
                        "provider_info": provider_config,
                        "voices": voices,
                        "recommended": engine.get_recommended_voices()
                    }
                    print(f"✅ 成功獲取 {provider} 引擎聲音列表: {len(voices)} 個聲音")
                else:
                    print(f"⚠️ {provider} 引擎不可用，跳過")
            except Exception as e:
                print(f"❌ 獲取 {provider} 引擎聲音列表失敗: {e}")
                # 繼續處理其他引擎，不讓單個引擎的錯誤影響整個系統
                continue
        return all_voices
    
    def get_provider_voices(self, provider: str) -> Dict[str, Any]:
        """獲取指定引擎的聲音列表"""
        engine = self.engines.get(provider)
        if not engine or not engine.is_available:
            return {}
        
        provider_config = self.config_manager.get_provider_config(provider)
        return {
            "provider": provider,
            "provider_info": provider_config,
            "voices": engine.get_available_voices(),
            "recommended": engine.get_recommended_voices()
        }
    
    async def close(self):
        """關閉所有引擎"""
        for engine in self.engines.values():
            try:
                await engine.close()
            except:
                pass


# 全局雙引擎管理器實例
dual_tts_manager = DualTTSManager()
