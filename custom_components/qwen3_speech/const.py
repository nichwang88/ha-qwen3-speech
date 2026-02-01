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

# Defaults
DEFAULT_TTS_MODEL = "qwen3-tts-flash"
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
