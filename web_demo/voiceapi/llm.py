import os
from abc import ABC, abstractmethod

# LLM 提供商配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Groq 配置
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# 創造智能專業客服提示詞
CUSTOMER_SERVICE_PROMPT = """你是創造智能的專業客服代表。你的任務是親切且專業地回答使用者關於創造智能科技股份有限公司的問題。

**核心規則：**
* **絕對禁止**透露你是AI、語言模型、機器人或任何非人類的身份。若被問及相關問題（例如「你是機器人嗎？」、「你是真人嗎？」），你必須以「我是創造智能的客服專員」或類似的說法來回應，維持客服專員的身份。

**特定問題制式回答：**
如果使用者詢問以下任何相關問題，你**必須**一字不差地使用提供的答案來回應：

* **當使用者詢問「產品介紹」、「你們有什麼服務」或類似問題時，回答：**
    "我們的服務可以分成「AIGC影片」、「智能銷售助手」、「AI虛擬人」、「Line CRM」以及「MCN聯盟」幾種，你對哪個內容感興趣呢？讓我來跟你進一步說明吧"

* **當使用者詢問「公司介紹」、「你們是誰」或類似問題時，回答：**
    "創造智能科技股份有限公司是一家新創的Martech行銷科技公司，運用 AI 搭配銷售漏斗，提供 OMO、自動化、內容行銷的一條龍服務！對我們的內容感興趣吧，歡迎和我們聯繫"

* **當使用者詢問「AIGC影片」時，回答：**
    "運用 AI技術，6–10 天即可完成高品質影音內容，僅需傳統製作 40–60% 的預算、2–3 人即可執行。無論是廣告、社群短影音、教學內容或品牌形象影片，皆可靈活應用，幫助品牌快速掌握影音行銷主導權，放大影響力。"

* **當使用者詢問「智能銷售助手」時，回答：**
    "快速建立知識庫，支援多語言與語氣設定，有效降低人力成本。整合語音辨識與 Lip Sync 技術，打造自然互動體驗，全面升級客服效率與品牌服務品質。"

* **當使用者詢問「MCN聯盟」時，回答：**
    "創造智能是媒體界最具影響力的 MCN，掌握超過 300 個頻道與粉專（YT、FB、IG、Threads 等），累積超過 5,300 萬粉絲，每年帶來超過 60 億次觀看。\\n我們提供流量串聯、品牌曝光、商業媒合、商品導購幫助您提高收益。"

* **當使用者詢問「LINE CRM」時，回答：**
    "整合LINE平台行銷與顧客關係管理，內建多元素材庫、優惠碼功能與短連結產生器，輕鬆進行分眾推播與自動化行銷，提升互動效率與轉換率。"

* **當使用者詢問「AI虛擬人」時，回答：**
    "AI虛擬人，只要一張照片或短影片，即可生成不同風格的專屬形象，整合語音識別與互動畫面設計，靈活應對多元場景，成為品牌專屬的智慧分身，全面強化形象力與互動體驗。"

* **當使用者詢問「智能客服」時，回答：**
    "快速建立知識庫，支援多語言與語氣設定，全天候在線，有效降低人力成本。整合語音辨識與 Lip Sync 技術，打造自然互動體驗，全面升級客服效率與品牌服務品質。"

**其他問題處理原則：**
對於未列在上述清單中的問題，請基於你對創造智能的了解，以親切、自然的客服專員語氣回答。如果遇到你不知道如何回答的問題，或問題超出你的業務範圍，請回答：「這個問題可能需要我們的業務專家來為您提供更詳細的資訊，方便留下您的聯絡方式嗎？我請專人盡快與您聯繫。」"""

def get_standard_response(prompt):
    """檢查是否有標準回答"""
    prompt_lower = prompt.lower()
    
    # 產品介紹相關
    if any(keyword in prompt_lower for keyword in ["產品介紹", "你們有什麼服務", "服務介紹", "產品", "服務"]):
        return "我們的服務可以分成「AIGC影片」、「智能銷售助手」、「AI虛擬人」、「Line CRM」以及「MCN聯盟」幾種，你對哪個內容感興趣呢？讓我來跟你進一步說明吧"
    
    # 公司介紹相關
    if any(keyword in prompt_lower for keyword in ["公司介紹", "你們是誰", "公司", "創造智能"]):
        return "創造智能科技股份有限公司是一家新創的Martech行銷科技公司，運用 AI 搭配銷售漏斗，提供 OMO、自動化、內容行銷的一條龍服務！對我們的內容感興趣吧，歡迎和我們聯繫"
    
    # AIGC影片
    if "aigc" in prompt_lower or "影片" in prompt_lower:
        return "運用 AI技術，6–10 天即可完成高品質影音內容，僅需傳統製作 40–60% 的預算、2–3 人即可執行。無論是廣告、社群短影音、教學內容或品牌形象影片，皆可靈活應用，幫助品牌快速掌握影音行銷主導權，放大影響力。"
    
    # 智能銷售助手/智能客服
    if any(keyword in prompt_lower for keyword in ["智能銷售助手", "智能客服", "銷售助手", "客服"]):
        return "快速建立知識庫，支援多語言與語氣設定，全天候在線，有效降低人力成本。整合語音辨識與 Lip Sync 技術，打造自然互動體驗，全面升級客服效率與品牌服務品質。"
    
    # MCN聯盟
    if "mcn" in prompt_lower or "聯盟" in prompt_lower:
        return "創造智能是媒體界最具影響力的 MCN，掌握超過 300 個頻道與粉專（YT、FB、IG、Threads 等），累積超過 5,300 萬粉絲，每年帶來超過 60 億次觀看。\n我們提供流量串聯、品牌曝光、商業媒合、商品導購幫助您提高收益。"
    
    # LINE CRM
    if "line" in prompt_lower or "crm" in prompt_lower:
        return "整合LINE平台行銷與顧客關係管理，內建多元素材庫、優惠碼功能與短連結產生器，輕鬆進行分眾推播與自動化行銷，提升互動效率與轉換率。"
    
    # AI虛擬人
    if any(keyword in prompt_lower for keyword in ["ai虛擬人", "虛擬人", "數位人"]):
        return "AI虛擬人，只要一張照片或短影片，即可生成不同風格的專屬形象，整合語音識別與互動畫面設計，靈活應對多元場景，成為品牌專屬的智慧分身，全面強化形象力與互動體驗。"
    
    # 身份相關問題
    if any(keyword in prompt_lower for keyword in ["你是機器人", "你是ai", "你是真人", "你是什麼"]):
        return "我是創造智能的客服專員，很高興為您服務！有什麼可以幫助您的嗎？"
    
    return None

# 抽象 LLM 提供商基類
class LLMProvider(ABC):
    @abstractmethod
    def stream_response(self, prompt):
        """流式回應"""
        pass
    
    @abstractmethod
    def get_response(self, prompt):
        """非流式回應"""
        pass
    
    @abstractmethod
    def is_available(self):
        """檢查提供商是否可用"""
        pass

# Groq 提供商實現
class GroqProvider(LLMProvider):
    def __init__(self):
        self.client = None
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self._init_client()
    
    def _init_client(self):
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            print("⚠️ 警告：Groq API 密鑰未配置")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key,
            )
            print("✅ Groq LLM 客戶端初始化成功")
        except Exception as e:
            print(f"❌ Groq LLM 客戶端初始化失敗: {e}")
            self.client = None
    
    def is_available(self):
        return self.client is not None
    
    def stream_response(self, prompt):
        if not self.is_available():
            return
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CUSTOMER_SERVICE_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                max_tokens=500,
                temperature=0.7,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"❌ Groq API 調用失敗: {e}")
            return
    
    def get_response(self, prompt):
        if not self.is_available():
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CUSTOMER_SERVICE_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Groq API 調用失敗: {e}")
            return None

# Gemini 提供商實現
class GeminiProvider(LLMProvider):
    def __init__(self):
        self.client = None
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self._init_client()
    
    def _init_client(self):
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("⚠️ 警告：Gemini API 密鑰未配置")
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            print("✅ Gemini LLM 客戶端初始化成功")
        except Exception as e:
            print(f"❌ Gemini LLM 客戶端初始化失敗: {e}")
            self.client = None
    
    def is_available(self):
        return self.client is not None
    
    def stream_response(self, prompt):
        if not self.is_available():
            return
        
        try:
            full_prompt = f"{CUSTOMER_SERVICE_PROMPT}\n\n用戶問題：{prompt}"
            response = self.client.generate_content(
                full_prompt,
                stream=True,
                generation_config={
                    "max_output_tokens": 500,
                    "temperature": 0.7,
                }
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"❌ Gemini API 調用失敗: {e}")
            return
    
    def get_response(self, prompt):
        if not self.is_available():
            return None
        
        try:
            full_prompt = f"{CUSTOMER_SERVICE_PROMPT}\n\n用戶問題：{prompt}"
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": 500,
                    "temperature": 0.7,
                }
            )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini API 調用失敗: {e}")
            return None

# LLM 管理器
class LLMManager:
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        self.fallback_providers = []
        self._init_providers()
    
    def _init_providers(self):
        # 初始化所有提供商
        self.providers['groq'] = GroqProvider()
        self.providers['gemini'] = GeminiProvider()
        
        # 設置主要提供商
        if LLM_PROVIDER in self.providers:
            self.primary_provider = self.providers[LLM_PROVIDER]
            print(f"🎯 主要 LLM 提供商: {LLM_PROVIDER}")
        
        # 設置備用提供商
        for name, provider in self.providers.items():
            if name != LLM_PROVIDER and provider.is_available():
                self.fallback_providers.append(provider)
        
        if self.fallback_providers:
            print(f"🔄 備用 LLM 提供商: {len(self.fallback_providers)} 個")
    
    def _get_available_provider(self):
        """獲取可用的提供商"""
        if self.primary_provider and self.primary_provider.is_available():
            return self.primary_provider
        
        for provider in self.fallback_providers:
            if provider.is_available():
                return provider
        
        return None
    
    def stream_response(self, prompt):
        """流式回應"""
        # 首先檢查標準回答
        standard_response = get_standard_response(prompt)
        if standard_response:
            for char in standard_response:
                yield char
            return
        
        # 嘗試使用 LLM
        provider = self._get_available_provider()
        if provider:
            try:
                for chunk in provider.stream_response(prompt):
                    if chunk:
                        yield chunk
                return
            except Exception as e:
                print(f"❌ LLM 流式回應失敗: {e}")
        
        # 降級到標準回答
        fallback_response = "感謝您的詢問！這個問題可能需要我們的業務專家來為您提供更詳細的資訊，方便留下您的聯絡方式嗎？我請專人盡快與您聯繫。"
        for char in fallback_response:
            yield char
    
    def get_response(self, prompt):
        """非流式回應"""
        # 首先檢查標準回答
        standard_response = get_standard_response(prompt)
        if standard_response:
            return standard_response
        
        # 嘗試使用 LLM
        provider = self._get_available_provider()
        if provider:
            response = provider.get_response(prompt)
            if response:
                return response
        
        # 降級到標準回答
        return "感謝您的詢問！這個問題可能需要我們的業務專家來為您提供更詳細的資訊，方便留下您的聯絡方式嗎？我請專人盡快與您聯繫。"

# 全局 LLM 管理器實例
llm_manager = LLMManager()

# 向後兼容的函數
def llm_stream(prompt):
    """流式LLM回應（向後兼容）"""
    return llm_manager.stream_response(prompt)

def llm_answer(prompt):
    """非流式LLM回應（向後兼容）"""
    return llm_manager.get_response(prompt)
