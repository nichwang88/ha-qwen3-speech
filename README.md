# Qwen3 Speech - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for **Qwen3 TTS** (Text-to-Speech) and **Qwen3 STT** (Speech-to-Text) via Alibaba Cloud DashScope API.

## Features

- **TTS (Text-to-Speech)**: Uses `qwen3-tts-flash` model with 45+ voice options
- **STT (Speech-to-Text)**: Uses `qwen3-asr-flash` model for speech recognition
- **10 Languages**: Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian
- **Single Integration**: One API key configures both TTS and STT
- **HACS Compatible**: Easy installation via HACS

## Prerequisites

1. An Alibaba Cloud account
2. A DashScope API key from [Alibaba Cloud Bailian Console](https://bailian.console.aliyun.com)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu -> **Custom repositories**
3. Add `https://github.com/nichwang88/ha-qwen3-speech` with category **Integration**
4. Search for "Qwen3 Speech" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/qwen3_speech` to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**
2. Search for "Qwen3 Speech"
3. Enter your DashScope API key
4. Select a default TTS voice
5. Both TTS and STT entities will be created automatically

## Usage

### TTS

```yaml
service: tts.speak
target:
  entity_id: tts.qwen3_tts
data:
  message: "Hello, world!"
  language: "en"
  options:
    voice: "Cherry"
```

### STT

The STT entity (`stt.qwen3_stt`) can be used with:
- Voice Assistant pipelines
- Automations that process audio input

### Available Voices

Cherry, Serena, Ethan, Chelsie, Momo, Vivian, Moon, Maia, Kai, Nofish, Bella, Jennifer, Ryan, Katerina, Aiden, Eldric Sage, Mia, Mochi, Bellona, Vincent, Bunny, Neil, Elias, Arthur, Nini, Ebona, Seren, Pip, Stella, Bodega, Sonrisa, Alek, Dolce, Sohee, Ono Anna, Lenn, Emilien, Andre, Radio Gol, Jada, Dylan, Li, Marcus, Roy, Peter

### Supported Languages

| Code | Language |
|------|----------|
| zh | Chinese |
| en | English |
| ja | Japanese |
| ko | Korean |
| de | German |
| fr | French |
| ru | Russian |
| pt | Portuguese |
| es | Spanish |
| it | Italian |

## API Documentation

- [Qwen3-TTS-Flash](https://help.aliyun.com/zh/model-studio/qwen-tts)
- [Qwen3-ASR-Flash](https://help.aliyun.com/zh/model-studio/qwen-speech-recognition)

## License

MIT License
