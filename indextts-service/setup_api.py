#!/usr/bin/env python3
"""
IndexTTS API 安裝腳本
簡化版本，專門用於API部署
"""

import subprocess
import sys
import os

def run_command(cmd):
    """執行命令並顯示輸出"""
    print(f"執行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"錯誤: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    print("=== IndexTTS API 環境設置 ===")
    
    # 檢查Python版本
    if sys.version_info < (3, 8):
        print("錯誤: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"Python版本: {sys.version}")
    
    # 安裝ffmpeg
    print("\n1. 安裝ffmpeg...")
    if not run_command("pip install ffmpeg"):
        print("ffmpeg安裝失敗")
        sys.exit(1)
    
    # 安裝PyTorch (CUDA版本)
    print("\n2. 安裝PyTorch (CUDA 11.8)...")
    if not run_command("pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118"):
        print("PyTorch安裝失敗")
        sys.exit(1)
    
    # 安裝其他依賴
    print("\n3. 安裝其他API依賴...")
    if not run_command("pip install -r requirements.txt"):
        print("依賴安裝失敗")
        sys.exit(1)
    
    # 安裝IndexTTS包
    print("\n4. 安裝IndexTTS包...")
    if not run_command("pip install -e ."):
        print("IndexTTS包安裝失敗")
        sys.exit(1)
    
    # 下載模型檔案
    print("\n5. 下載模型檔案...")
    download_cmd = """huggingface-cli download IndexTeam/IndexTTS-1.5 \
  config.yaml bigvgan_discriminator.pth bigvgan_generator.pth bpe.model dvae.pth gpt.pth unigram_12000.vocab \
  --local-dir checkpoints"""
    
    if not run_command(download_cmd):
        print("模型下載失敗")
        print("請確保網路連接正常，或手動下載模型檔案")
        sys.exit(1)
    
    # 重新編譯CUDA kernel以獲得更好的性能
    print("\n6. 重新編譯CUDA kernel...")
    if not run_command("pip install -e . --no-deps --no-build-isolation"):
        print("警告: CUDA kernel編譯失敗，將使用fallback模式")
        print("這不影響基本功能，但可能影響性能")
    
    # 檢查模型檔案
    print("\n7. 檢查模型檔案...")
    required_files = [
        "checkpoints/config.yaml",
        "checkpoints/gpt.pth",
        "checkpoints/bigvgan_generator.pth",
        "checkpoints/bpe.model"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("警告: 缺少以下模型檔案:")
        for file in missing_files:
            print(f"  - {file}")
        print("請確保模型檔案已正確複製到checkpoints目錄")
    else:
        print("所有模型檔案檢查完成 ✓")
    
    print("\n=== 安裝完成 ===")
    print("啟動API服務:")
    print("  python api.py")
    print("\nAPI文檔:")
    print("  http://localhost:6008/docs")

if __name__ == "__main__":
    main()
