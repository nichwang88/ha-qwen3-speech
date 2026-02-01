# Qwen3 Speech - Home Assistant 集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

通过阿里云百炼 DashScope API，将**千问3语音合成（TTS）**和**千问3语音识别（STT）**接入 Home Assistant 的自定义集成。一个集成同时提供 TTS 和 STT 两项服务。

## 功能特性

- **语音合成（TTS）**：使用 `qwen3-tts-flash` 模型，支持 45+ 种音色
- **语音识别（STT）**：使用 `qwen3-asr-flash` 模型，支持语音转文字
- **10 种语言**：中文、英语、日语、韩语、德语、法语、俄语、葡萄牙语、西班牙语、意大利语
- **统一配置**：一个 API Key 同时启用 TTS 和 STT
- **可视化设置**：支持在集成设置界面修改 API Key、模型名称、音色、语速等参数
- **HACS 兼容**：支持通过 HACS 一键安装

## 前置条件

1. 阿里云账号
2. 从[阿里云百炼控制台](https://bailian.console.aliyun.com)获取 DashScope API Key

## 安装方式

### HACS 安装（推荐）

1. 打开 Home Assistant 中的 HACS
2. 点击右上角三点菜单 -> **自定义存储库**
3. 添加 `https://github.com/nichwang88/ha-qwen3-speech`，类别选择 **Integration**
4. 搜索 "Qwen3 Speech" 并安装
5. 重启 Home Assistant

### 手动安装

1. 将 `custom_components/qwen3_speech` 文件夹复制到 Home Assistant 的 `custom_components` 目录下
2. 重启 Home Assistant

## 配置说明

### 初次配置

1. 进入 **设置** -> **设备与服务** -> **添加集成**
2. 搜索 "Qwen3 Speech"
3. 填写以下信息：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| DashScope API Key | 阿里云百炼 API 密钥 | （必填） |
| TTS 模型 | 语音合成模型名称 | `qwen3-tts-flash` |
| STT 模型 | 语音识别模型名称 | `qwen3-asr-flash` |
| 默认音色 | TTS 默认使用的音色 | Cherry |
| 默认语速 | TTS 默认语速倍率（0.5-2.0） | 1.0 |

4. 提交后自动创建 TTS 和 STT 两个实体

### 修改设置

添加集成后，点击集成卡片上的 **配置** 按钮，可随时修改以上所有参数。修改后集成会自动重载生效。

## 使用方法

### 语音合成（TTS）

基本调用：

```yaml
service: tts.speak
target:
  entity_id: tts.qwen3_tts
data:
  message: "你好，世界！"
```

指定音色和语速：

```yaml
service: tts.speak
target:
  entity_id: tts.qwen3_tts
data:
  message: "Hello, world!"
  language: "en"
  options:
    voice: "Ethan"
    speed: 1.5
```

### 语音识别（STT）

STT 实体（`stt.qwen3_stt`）可用于：
- Voice Assistant 语音助手管道
- 处理音频输入的自动化

## 可用音色

Cherry, Serena, Ethan, Chelsie, Momo, Vivian, Moon, Maia, Kai, Nofish, Bella, Jennifer, Ryan, Katerina, Aiden, Eldric Sage, Mia, Mochi, Bellona, Vincent, Bunny, Neil, Elias, Arthur, Nini, Ebona, Seren, Pip, Stella, Bodega, Sonrisa, Alek, Dolce, Sohee, Ono Anna, Lenn, Emilien, Andre, Radio Gol, Jada, Dylan, Li, Marcus, Roy, Peter

## 支持语言

| 代码 | 语言 |
|------|------|
| zh | 中文 |
| en | 英语 |
| ja | 日语 |
| ko | 韩语 |
| de | 德语 |
| fr | 法语 |
| ru | 俄语 |
| pt | 葡萄牙语 |
| es | 西班牙语 |
| it | 意大利语 |

## API 文档

- [Qwen3-TTS-Flash 语音合成](https://help.aliyun.com/zh/model-studio/qwen-tts)
- [Qwen3-ASR-Flash 语音识别](https://help.aliyun.com/zh/model-studio/qwen-speech-recognition)

## 许可证

MIT License
