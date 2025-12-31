// DOM elements
const ttsForm = document.getElementById('ttsForm');
const ttsText = document.getElementById('ttsText');
const voiceSelect = document.getElementById('voiceSelect');
const generateBtn = document.getElementById('generateBtn');
const loading = document.getElementById('loading');
const resultsContainer = document.getElementById('resultsContainer');
const audioPlayer1 = document.getElementById('audioPlayer1');
const audioPlayer2 = document.getElementById('audioPlayer2');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const charCount = document.getElementById('charCount');

// Global variables
let audioBlobs = {
    1: null,
    2: null
};
let availableVoices = [];

// Demo 文字內容
const demoTexts = {
    1: "這是一個好日子！ 你吃飽了嗎？ 附近有家餐廳好吃喔。一起去吃吧！",
    2: "一開始查字典，慢慢地看簡體字，沒多久，就看得很順了！所以只要去學，就會了阿！寫台文也一樣，查一次記不得，查兩次，查三次……，總是會記起來。",
    3: "這個問題可能需要我們的業務專家來為您提供更詳細的資訊，方便留下您的聯絡方式嗎？我請專人盡快與您聯絡！"
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updateCharCount();
    loadVoices();
});

function setupEventListeners() {
    // Form submission
    ttsForm.addEventListener('submit', handleFormSubmit);
    
    // Character count
    ttsText.addEventListener('input', updateCharCount);
    
    // Demo buttons
    document.querySelectorAll('.demo-btn').forEach(btn => {
        btn.addEventListener('click', handleDemoClick);
    });
}

function updateCharCount() {
    const count = ttsText.value.length;
    charCount.textContent = count;
    
    if (count > 500) {
        charCount.style.color = '#e53e3e';
    } else if (count > 400) {
        charCount.style.color = '#dd6b20';
    } else {
        charCount.style.color = '#666';
    }
}

async function loadVoices() {
    try {
        const response = await fetch('/api/voices');
        if (!response.ok) {
            throw new Error('無法載入聲音配置');
        }
        
        const data = await response.json();
        availableVoices = data.voices;
        
        // 清空現有選項
        voiceSelect.innerHTML = '';
        
        // 添加聲音選項
        availableVoices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = `${voice.name} - ${voice.description}`;
            voiceSelect.appendChild(option);
        });
        
        // 自動選擇第一個聲音
        if (availableVoices.length > 0) {
            voiceSelect.value = availableVoices[0].id;
        }
        
    } catch (error) {
        console.error('載入聲音配置失敗:', error);
        showError('載入聲音配置失敗，請重新整理頁面');
    }
}

function handleDemoClick(event) {
    const demoNumber = event.currentTarget.getAttribute('data-demo');
    const demoText = demoTexts[demoNumber];
    
    // 檢查是否選擇了聲音
    if (!voiceSelect.value) {
        showError('請先選擇聲音類型');
        voiceSelect.focus();
        return;
    }
    
    // 填入 demo 文字
    ttsText.value = demoText;
    updateCharCount();
    
    // 自動觸發生成
    const text = demoText;
    const voiceId = voiceSelect.value;
    
    // Show loading and results container
    showLoading();
    hideError();
    showResultsContainer();
    
    try {
        // 顯示兩個 loading
        showResultLoading(1);
        showResultLoading(2);
        
        // 版本1: 先翻譯成台語再生成
        generateAudioWithTranslation(text, voiceId, 1);
        
        // 版本2: 直接使用原文生成
        generateAudioAsync(text, voiceId, 2);
        
    } catch (error) {
        console.error('Error:', error);
        showError('生成語音時發生錯誤: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Validate form
    if (!validateForm()) {
        return;
    }
    
    // Show loading and results container
    showLoading();
    hideError();
    showResultsContainer();
    
    try {
        const text = ttsText.value.trim();
        const selectedVoiceId = voiceSelect.value;
        
        // 顯示兩個 loading
        showResultLoading(1);
        showResultLoading(2);
        
        // 版本1: 先翻譯成台語再生成
        generateAudioWithTranslation(text, selectedVoiceId, 1);
        
        // 版本2: 直接使用原文生成
        generateAudioAsync(text, selectedVoiceId, 2);
        
    } catch (error) {
        console.error('Error:', error);
        showError('生成語音時發生錯誤: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function translateToTaiwanese(text) {
    try {
        const response = await fetch('https://learn-language.tokyo/taigiTranslator/model2/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                inputText: text,
                inputLan: "Traditional Chinese:zhTW",
                outputLan: "Taiwanese:tw"
            })
        });
        
        if (!response.ok) {
            throw new Error(`翻譯失敗: ${response.status}`);
        }
        
        const data = await response.json();
        return data.outputText || data.result || text; // 根據實際 API 回應調整
        
    } catch (error) {
        console.error('Translation error:', error);
        throw new Error('台語翻譯失敗，請稍後再試');
    }
}

async function generateAudioWithTranslation(text, voiceId, version) {
    try {
        // 先翻譯成台語
        const translatedText = await translateToTaiwanese(text);
        console.log('翻譯結果:', translatedText);
        
        // 使用翻譯後的文字生成語音
        const formData = new FormData();
        formData.append('tts_text', translatedText);
        formData.append('voice_id', voiceId);
        formData.append('original_text', text); // 傳遞原始文字給後端記錄
        
        const response = await fetch('/api/inference_with_voice_config', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        audioBlobs[version] = blob;
        
        // 創建音頻 URL 並設置播放器
        const audioUrl = URL.createObjectURL(blob);
        const audioPlayer = document.getElementById(`audioPlayer${version}`);
        audioPlayer.src = audioUrl;
        
        // 隱藏 loading 並顯示音頻播放器
        hideResultLoading(version);
        showAudioContent(version);
        
    } catch (error) {
        console.error(`Error generating audio ${version}:`, error);
        hideResultLoading(version);
        showError(`語音版本 ${version} 生成失敗: ${error.message}`);
    }
}

async function generateAudioAsync(text, voiceId, version) {
    try {
        // 找出對應的聲音配置
        const voiceConfig = availableVoices.find(v => v.id === voiceId);
        if (!voiceConfig) {
            throw new Error('找不到聲音配置');
        }
        
        // 準備 API 請求數據 (JSON 格式)
        // 假設 voiceId 對應到新 API 的 character 參數
        const payload = {
            "text": text,
            "character": voiceId, // 使用選擇的 voice ID 作為角色
            "seed": voiceConfig.seed || 2 // 如果配置有 seed 就用，沒有就用默認值 2
        };
        
        console.log('Calling external TTS:', payload);

        // 通過 nginx 代理調用外部 API
        const response = await fetch('/external-tts/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        audioBlobs[version] = blob;
        
        // 創建音頻 URL 並設置播放器
        const audioUrl = URL.createObjectURL(blob);
        const audioPlayer = document.getElementById(`audioPlayer${version}`);
        audioPlayer.src = audioUrl;
        
        // 隱藏 loading 並顯示音頻播放器
        hideResultLoading(version);
        showAudioContent(version);
        
    } catch (error) {
        console.error(`Error generating audio ${version}:`, error);
        hideResultLoading(version);
        showError(`語音版本 ${version} 生成失敗: ${error.message}`);
    }
}

function validateForm() {
    // Check text input
    if (!ttsText.value.trim()) {
        showError('請輸入要轉換的文字');
        ttsText.focus();
        return false;
    }
    
    if (ttsText.value.length > 500) {
        showError('文字長度不能超過 500 字元');
        ttsText.focus();
        return false;
    }
    
    // Check voice selection
    if (!voiceSelect.value) {
        showError('請選擇聲音類型');
        voiceSelect.focus();
        return false;
    }
    
    return true;
}

function showLoading() {
    loading.style.display = 'block';
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>生成中...</span>';
}

function hideLoading() {
    loading.style.display = 'none';
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<i class="fas fa-play"></i><span>生成語音</span>';
}

function showResultsContainer() {
    resultsContainer.style.display = 'block';
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideResultsContainer() {
    resultsContainer.style.display = 'none';
}

function showResultLoading(version) {
    const loadingEl = document.getElementById(`loading${version}`);
    const audioContent = document.getElementById(`audioContent${version}`);
    
    loadingEl.style.display = 'block';
    audioContent.style.display = 'none';
}

function hideResultLoading(version) {
    const loadingEl = document.getElementById(`loading${version}`);
    loadingEl.style.display = 'none';
}

function showAudioContent(version) {
    const audioContent = document.getElementById(`audioContent${version}`);
    audioContent.style.display = 'block';
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    errorMessage.style.display = 'none';
}

function downloadAudio(version) {
    if (!audioBlobs[version]) {
        showError('沒有可下載的音頻檔案');
        return;
    }
    
    const url = URL.createObjectURL(audioBlobs[version]);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_voice_v${version}_${Date.now()}.wav`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Add some CSS for the select dropdown
const style = document.createElement('style');
style.textContent = `
    select {
        padding: 15px;
        border: 2px solid #e1e5e9;
        border-radius: 12px;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
        width: 100%;
        cursor: pointer;
    }
    
    select:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    select option {
        padding: 10px;
    }
`;
document.head.appendChild(style);

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (!generateBtn.disabled) {
            handleFormSubmit(event);
        }
    }
    
    // Escape to hide error
    if (event.key === 'Escape') {
        hideError();
    }
});

// Add tooltips for better UX
function addTooltips() {
    const tooltips = {
        'ttsText': '輸入您想要轉換成語音的文字內容',
        'voiceSelect': '選擇適合的聲音風格和語調'
    };
    
    Object.entries(tooltips).forEach(([id, text]) => {
        const element = document.getElementById(id);
        if (element) {
            element.title = text;
        }
    });
}

// Initialize tooltips
addTooltips();

// Performance optimization: Debounce character count update
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Replace the direct event listener with debounced version
ttsText.removeEventListener('input', updateCharCount);
ttsText.addEventListener('input', debounce(updateCharCount, 100));
