#!/usr/bin/env python3
"""
Warmup script to initialize the model with a test inference
This prevents the first real request from timing out
"""
import time
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_service(url, max_retries=60, retry_interval=2):
    """Wait for the service to become available"""
    logger.info(f"Waiting for service at {url}...")
    for i in range(max_retries):
        try:
            # Use /voices endpoint to check if service is ready
            response = requests.get(f"{url}/voices", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Service is ready!")
                return True
        except requests.exceptions.RequestException as e:
            pass
        
        if i < max_retries - 1:
            time.sleep(retry_interval)
            if (i + 1) % 10 == 0:
                logger.info(f"Still waiting... ({i + 1}/{max_retries})")
    
    logger.error(f"Service did not become available after {max_retries * retry_interval} seconds")
    return False

def warmup_inference(url, config_file="/opt/CosyVoice/config/voices.local.json"):
    """Perform a warmup inference request"""
    logger.info("Starting warmup inference...")
    
    # Load voice configuration
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            voices_data = json.load(f)
        
        # Extract voices list from the configuration
        voices_list = voices_data.get("voices", [])
        
        # Use the first voice configuration
        if voices_list and len(voices_list) > 0:
            voice_config = voices_list[0]
            voice_name = voice_config.get("name", voice_config.get("id", "unknown"))
            logger.info(f"Using voice configuration: {voice_name}")
        else:
            # Fallback configuration
            voice_config = {
                "seed": 0
            }
            logger.info("Using fallback configuration")
    except Exception as e:
        logger.warning(f"Could not load voice config: {e}, using fallback")
        voice_config = {
            "seed": 0,
            "id": "warmup"
        }
    
    # Prepare warmup request with correct parameters
    warmup_data = {
        "tts_text": "你好",
        "voice_id": voice_config.get("id", "gentle_female")
    }
    
    try:
        logger.info("Sending warmup request...")
        response = requests.post(
            f"{url}/inference_with_voice_config",
            data=warmup_data,
            timeout=300  # 5 minutes timeout for first inference
        )
        
        if response.status_code == 200:
            logger.info(f"✓ Warmup successful! Audio size: {len(response.content)} bytes")
            logger.info("=" * 60)
            logger.info("🎉 System is fully warmed up and ready to serve!")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"✗ Warmup failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("✗ Warmup request timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Warmup failed with error: {e}")
        return False

def main():
    service_url = "http://localhost:50001"
    
    # Wait for service to start
    if not wait_for_service(service_url):
        logger.error("Service failed to start, skipping warmup")
        return 1 
    
    # Give the service a bit more time to fully initialize
    logger.info("Waiting additional 5 seconds for full initialization...")
    time.sleep(5)
    
    # Perform warmup
    if warmup_inference(service_url):
        logger.info("Warmup completed successfully!")
        return 0
    else:
        logger.warning("Warmup failed, but service is running")
        return 0  # Don't fail the container startup

if __name__ == "__main__":
    exit(main())
