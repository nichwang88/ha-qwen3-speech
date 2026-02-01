"""Constants for the Qwen3 Speech integration."""

DOMAIN = "qwen3_speech"

# DashScope API
DASHSCOPE_API_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
)

# Models
TTS_MODEL = "qwen3-tts-flash"
ASR_MODEL = "qwen3-asr-flash"

# Config keys
CONF_API_KEY = "api_key"
CONF_VOICE = "voice"
CONF_LANGUAGE = "language"

# Defaults
DEFAULT_VOICE = "Cherry"
DEFAULT_LANGUAGE = "Auto"

# Available voices (49 total)
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
