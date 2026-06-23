"""Constants for the Qwen3 Speech integration."""

DOMAIN = "qwen3_speech"

# DashScope API
DASHSCOPE_API_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
)

# Config keys
CONF_API_KEY = "api_key"
CONF_TTS_MODEL = "tts_model"
CONF_STT_MODEL = "stt_model"
CONF_VOICE = "voice"
CONF_SPEED = "speed"
CONF_INSTRUCTIONS = "instructions"

# Defaults
DEFAULT_TTS_MODEL = "qwen3-tts-flash"
# Emotion/instruction control needs an "instruct" model (e.g. qwen3-tts-instruct-flash).
# Default instructions: "" = none, "auto" = pick emotion from the text content.
DEFAULT_INSTRUCTIONS = ""
AUTO_INSTRUCTIONS = "auto"
DEFAULT_STT_MODEL = "qwen3-asr-flash"
DEFAULT_VOICE = "Cherry"
DEFAULT_LANGUAGE = "Auto"
DEFAULT_SPEED = 1.0

# Speed range
MIN_SPEED = 0.5
MAX_SPEED = 2.0

# Available voices
VOICES = [
    "Cherry",
    "Serena",
    "Ethan",
    "Chelsie",
    "Momo",
    "Vivian",
    "Moon",
    "Maia",
    "Kai",
    "Nofish",
    "Bella",
    "Jennifer",
    "Ryan",
    "Katerina",
    "Aiden",
    "Eldric Sage",
    "Mia",
    "Mochi",
    "Bellona",
    "Vincent",
    "Bunny",
    "Neil",
    "Elias",
    "Arthur",
    "Nini",
    "Ebona",
    "Seren",
    "Pip",
    "Stella",
    "Bodega",
    "Sonrisa",
    "Alek",
    "Dolce",
    "Sohee",
    "Ono Anna",
    "Lenn",
    "Emilien",
    "Andre",
    "Radio Gol",
    "Jada",
    "Dylan",
    "Li",
    "Marcus",
    "Roy",
    "Peter",
]

# Language code to DashScope language_type mapping
LANGUAGE_MAP = {
    "zh": "Chinese",
    "en": "English",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "es": "Spanish",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "ru": "Russian",
}

# Supported language codes
SUPPORT_LANGUAGES = list(LANGUAGE_MAP.keys())

# TTS text limit
TTS_MAX_CHARS = 600

# --- Content-aware emotion (for instruct models, when instructions == "auto") ---
# Each rule: (keywords, instruction). First matching rule (top priority first) wins.
# The instruction is natural-language style guidance passed to the instruct model.
AUTO_EMOTION_RULES = [
    (
        ("低电量", "电量不足", "警告", "告警", "故障", "异常", "紧急", "危险", "断开连接"),
        "用沉稳、严肃、可信赖的语气说话",
    ),
    (
        ("生日", "恭喜", "新年", "春节", "中秋", "元旦", "国庆", "清明", "端午",
         "劳动节", "儿童节", "情人节", "圣诞", "节日", "佳节"),
        "用开朗、喜悦、热情洋溢的语气说话",
    ),
    (
        ("晚安", "夜晚", "睡前", "入睡", "晚上好", "傍晚"),
        "用温柔、平静、放松的语气说话",
    ),
    (
        ("雨", "雪", "阴", "降温", "寒潮", "雾", "霾", "台风", "大风"),
        "用温柔、治愈、舒缓的语气说话",
    ),
    (
        ("晴", "阳光", "早上好", "早安", "上午好", "多云"),
        "用温暖、明亮、有活力的语气说话",
    ),
]
DEFAULT_EMOTION = "用温柔、自然、亲切的语气说话"


def pick_emotion(text: str) -> str:
    """Pick an emotion instruction from text content (rule-based)."""
    for keywords, instruction in AUTO_EMOTION_RULES:
        if any(kw in text for kw in keywords):
            return instruction
    return DEFAULT_EMOTION
