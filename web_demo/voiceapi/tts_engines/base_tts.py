"""
TTS 引擎基礎抽象類
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class BaseTTSEngine(ABC):
    """TTS 引擎基礎抽象類"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_available = False
        self.provider_name = config.get("provider", "unknown")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化 TTS 引擎
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def generate_audio(self, text: str, voice_id: str, **kwargs) -> Optional[str]:
        """
        生成音頻
        
        Args:
            text: 要合成的文本
            voice_id: 聲音 ID
            **kwargs: 其他參數（如語速等）
            
        Returns:
            Optional[str]: Base64 編碼的音頻數據，失敗時返回 None
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取可用的聲音列表
        
        Returns:
            Dict[str, Dict[str, Any]]: 聲音 ID 到聲音配置的映射
        """
        pass
    
    def get_recommended_voices(self) -> List[str]:
        """
        獲取推薦的聲音列表
        
        Returns:
            List[str]: 推薦的聲音 ID 列表
        """
        voices = self.get_available_voices()
        return [
            voice_id for voice_id, voice_config in voices.items()
            if voice_config.get("recommended", False)
        ]
    
    def get_default_voice(self) -> str:
        """
        獲取默認聲音 ID
        
        Returns:
            str: 默認聲音 ID
        """
        return self.config.get("default_voice", "")
    
    async def close(self):
        """關閉引擎，清理資源"""
        pass
