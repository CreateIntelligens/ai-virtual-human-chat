#!/usr/bin/env python3
"""
TTS API 使用範例 - 包含 seed 參數和詞庫功能
"""

import requests
import json

# API 服務器地址
API_BASE_URL = "http://localhost:11996"

def example_tts_with_text_processing():
    """使用 /tts 端點的範例，展示完整的文字處理功能"""
    print("=== /tts 端點使用範例（包含文字處理）===")
    
    payload = {
        "text": "三立新聞台報導，AI 技術在 TTS 領域和資訊科技方面取得重大進展",
        "character": "your_character_name",  # 請替換為實際的角色名稱
        "seed": 42  # 設定 seed 以獲得可重現的結果
    }
    
    print(f"請求 payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    print(f"\n預期的文字處理流程:")
    print(f"1. 詞庫轉換: '三立' -> '(三立)', 'AI' -> '人工智慧', 'TTS' -> '語音合成'")
    print(f"2. 繁簡轉換: '資訊科技' -> '信息科技', '語音合成' -> '语音合成'")
    print(f"3. 最終文字: '(三立)新闻台报道，人工智能技术在语音合成领域和信息科技方面取得重大进展'")
    
    try:
        response = requests.post(f"{API_BASE_URL}/tts", json=payload)
        
        if response.status_code == 200:
            # 保存音頻文件
            with open("output_tts_processed.wav", "wb") as f:
                f.write(response.content)
            print("\n✓ 成功生成語音，已保存為 output_tts_processed.wav")
            print("  語音基於處理後的簡體中文文字生成")
        else:
            print(f"✗ 請求失敗: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                print(f"錯誤訊息: {response.json()}")
                
    except Exception as e:
        print(f"錯誤: {e}")

def example_audio_speech_with_seed():
    """使用 /audio/speech 端點的範例，包含 seed 參數"""
    print("\n=== /audio/speech 端點使用範例 (OpenAI 兼容) ===")
    
    payload = {
        "input": "這個 API 支援自定義詞庫和 seed 參數功能",
        "voice": "your_character_name",  # 請替換為實際的角色名稱
        "model": "your_model_name",      # 請替換為實際的模型名稱
        "seed": 123  # 設定不同的 seed 值
    }
    
    print(f"請求 payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    
    try:
        response = requests.post(f"{API_BASE_URL}/audio/speech", json=payload)
        
        if response.status_code == 200:
            # 保存音頻文件
            with open("output_speech.wav", "wb") as f:
                f.write(response.content)
            print("✓ 成功生成語音，已保存為 output_speech.wav")
            print("  詞庫轉換: 'API' -> '應用程式介面'")
        else:
            print(f"✗ 請求失敗: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                print(f"錯誤訊息: {response.json()}")
                
    except Exception as e:
        print(f"錯誤: {e}")

def example_tts_url_with_seed():
    """使用 /tts_url 端點的範例，包含 seed 參數"""
    print("\n=== /tts_url 端點使用範例 ===")
    
    payload = {
        "text": "JSON 格式的資料透過 HTTP 協定傳輸",
        "audio_paths": ["/path/to/your/reference/audio.wav"],  # 請替換為實際的音頻文件路徑
        "seed": 999  # 設定 seed 值
    }
    
    print(f"請求 payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("(註: 需要提供有效的參考音頻文件路徑)")

def compare_seed_effects():
    """比較不同 seed 值的效果"""
    print("\n=== 比較不同 Seed 值的效果 ===")
    
    base_payload = {
        "text": "測試相同文本在不同 seed 下的語音效果",
        "character": "your_character_name"  # 請替換為實際的角色名稱
    }
    
    seeds = [1, 42, 100]
    
    for seed in seeds:
        payload = base_payload.copy()
        payload["seed"] = seed
        
        print(f"\n使用 seed={seed}:")
        print(f"  相同的文本和角色設定")
        print(f"  期望: 每次使用相同 seed 會產生相同的語音")
        
        # 這裡可以實際調用 API 並比較結果
        # (需要有效的角色設定)

def test_text_processing_api():
    """測試文字處理 API"""
    print("\n=== 測試文字處理 API ===")
    
    test_text = "三立新聞台報導，資訊科技和AI技術發展迅速"
    
    try:
        payload = {"text": test_text}
        response = requests.post(f"{API_BASE_URL}/test_text_processing", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"原始文字: {data['original_text']}")
            print(f"詞庫轉換後: {data['after_dict_conversion']}")
            print(f"最終結果: {data['final_text']}")
            print(f"OpenCC 可用: {data['opencc_available']}")
        else:
            print(f"測試失敗: {response.status_code}")
            
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    print("TTS API 使用範例 - 完整文字處理功能\n")
    
    # 檢查服務狀態
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✓ TTS 服務運行正常\n")
        else:
            print("✗ TTS 服務可能未啟動")
            exit(1)
    except:
        print("✗ 無法連接到 TTS 服務")
        exit(1)
    
    # 測試文字處理 API
    test_text_processing_api()
    
    # 顯示使用範例
    example_tts_with_text_processing()
    example_audio_speech_with_seed() 
    example_tts_url_with_seed()
    compare_seed_effects()
    
    print(f"\n注意事項:")
    print(f"1. 請將範例中的 'your_character_name' 替換為實際可用的角色名稱")
    print(f"2. 請將 'your_model_name' 替換為實際的模型名稱")
    print(f"3. 請將音頻路徑替換為實際存在的文件路徑") 
    print(f"4. seed 參數是可選的，預設值為 8")
    print(f"5. 相同的 seed 值會產生相同的語音輸出，確保結果可重現")
    print(f"6. 所有 TTS API 都會自動進行文字處理（詞庫轉換 + 繁簡轉換）")
    print(f"7. 可使用 /test_text_processing 端點測試文字轉換效果")
