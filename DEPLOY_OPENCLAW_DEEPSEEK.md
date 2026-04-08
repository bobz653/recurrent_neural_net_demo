# 本地部署 OpenClaw + DeepSeek 指南

本文档介绍如何在本地部署 OpenClaw 服务，并连接本地部署的 DeepSeek 模型作为推理后端。

## 整体架构

```
本地 DeepSeek 模型 (Ollama/vLLM)  ←→  OpenClaw Gateway  ←→  消息平台 / Web UI
         (推理引擎)                     (AI 助手框架)          (用户交互)
```

## 前置条件

- Linux / macOS / Windows (WSL)
- Node.js 24（推荐）或 Node.js 22.16+
- GPU（本地运行 DeepSeek 模型需要，14B 模型至少 10GB 显存）
- npm / pnpm / bun（包管理器）

## 阶段一：部署本地 DeepSeek 推理服务

### 方案 A：使用 Ollama（推荐，简单易用）

1. 安装 Ollama：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. 拉取 DeepSeek 模型（根据 GPU 显存选择）：

```bash
# 14B 参数，需要约 10GB 显存
ollama pull deepseek-r1:14b

# 32B 参数，需要约 20GB 显存（效果更好）
ollama pull deepseek-r1:32b

# 代码场景轻量模型
ollama pull deepseek-coder:6.7b

# 支持 tool-calling 的 DeepSeek 变体（推荐用于 OpenClaw）
ollama pull MFDoom/deepseek-r1-tool-calling:14b
```

3. 启动 Ollama 服务：

```bash
ollama serve
```

默认监听地址：`http://localhost:11434`
OpenAI 兼容 API 地址：`http://127.0.0.1:11434/v1`
API Key：任意值即可（如 `ollama-local`，Ollama 不验证 key）

4. 验证服务正常：

```bash
curl http://localhost:11434/api/tags
```

### 方案 B：使用 vLLM（高性能，适合生产环境）

1. 安装 vLLM：

```bash
pip install vllm
```

2. 启动 DeepSeek 服务：

```bash
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-14B --port 8000
```

默认 API 地址：`http://127.0.0.1:8000/v1`
API Key：任意值即可

3. 验证服务正常：

```bash
curl http://localhost:8000/v1/models
```

## 阶段二：安装 OpenClaw

1. 全局安装 OpenClaw：

```bash
npm install -g openclaw@latest
```

2. 运行引导设置向导：

```bash
openclaw onboard --install-daemon
```

向导交互步骤：
- Onboarding mode → 选择 `Quickstart`
- Model/auth provider → 选择 `Custom Provider`
- API Base URL → 输入本地 DeepSeek 地址，如 `http://127.0.0.1:11434/v1`（Ollama）或 `http://127.0.0.1:8000/v1`（vLLM）
- API Key → 输入本地 API Key（如 `ollama-local`）
- Model ID → 输入模型 ID，如 `deepseek-r1:14b`
- Model alias → 设置为 `deepseek`（或任意名称）

## 阶段三：手动配置（可选）

如果需要更精细的控制，可以手动编辑 `~/.openclaw/openclaw.json`：

### Ollama + DeepSeek 配置示例

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "ollama/deepseek-r1:14b",
            "name": "DeepSeek R1 14B (Local)",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 131072,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/deepseek-r1:14b"
      }
    }
  }
}
```

### vLLM + DeepSeek 配置示例

```json
{
  "models": {
    "providers": {
      "deepseek-local": {
        "baseUrl": "http://127.0.0.1:8000/v1",
        "apiKey": "vllm-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "deepseek-local/deepseek-r1-14b",
            "name": "DeepSeek R1 14B (vLLM)",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 131072,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek-local/deepseek-r1-14b"
      }
    }
  }
}
```

### 自定义 DeepSeek API 地址和 Key

如果你使用的是自部署的 DeepSeek API 服务（非 Ollama/vLLM），只需将 `baseUrl` 和 `apiKey` 替换为实际值：

```json
{
  "models": {
    "providers": {
      "deepseek-custom": {
        "baseUrl": "http://YOUR_DEEPSEEK_HOST:YOUR_PORT/v1",
        "apiKey": "YOUR_DEEPSEEK_API_KEY",
        "api": "openai-completions",
        "models": [
          {
            "id": "deepseek-custom/deepseek-chat",
            "name": "DeepSeek Chat (Self-hosted)",
            "reasoning": false,
            "input": ["text"],
            "contextWindow": 128000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek-custom/deepseek-chat"
      }
    }
  }
}
```

## 阶段四：启动和验证

1. 启动/重启 OpenClaw Gateway：

```bash
openclaw gateway --force
```

2. 检查状态：

```bash
openclaw status
```

3. 打开 Web UI 进行测试对话：

```
http://127.0.0.1:18789
```

4. 检查配置是否正确：

```
http://127.0.0.1:18789/config
```

## 配置关键说明

| 配置项 | 说明 |
|--------|------|
| `baseUrl` | 本地 DeepSeek 服务地址。Ollama 默认 `11434` 端口，vLLM 默认 `8000` 端口 |
| `apiKey` | 本地 API Key。Ollama 不验证，可随意填写；其他方式填真实 key |
| `api` | 必须设为 `"openai-completions"`，DeepSeek 兼容 OpenAI 格式 |
| `contextWindow` | 建议至少 16000（OpenClaw 最低要求），DeepSeek 支持 128K+ |
| `cost` | 本地推理全部设为 0 |
| `reasoning` | DeepSeek-R1 系列设为 `true`，DeepSeek-Chat 设为 `false` |

## 注意事项

1. **模型大小**：OpenClaw 的系统提示词约 4-6K tokens，加上工具定义会更大。建议至少使用 14B 参数模型，7B 以下可能无法稳定处理 tool calling。

2. **Tool Calling 支持**：OpenClaw 大量使用 function/tool calling。确保选择的模型支持此功能，推荐使用 `MFDoom/deepseek-r1-tool-calling:14b` 或 `deepseek-coder` 系列。

3. **Reasoning 模型兼容性**：DeepSeek Reasoner 的 `reasoning_content` 字段可能被 OpenClaw 的消息规范化器剥离。如果遇到问题，优先尝试 `deepseek-chat` 类型模型。

4. **API 模式选择**：
   - `"api": "openai-completions"` — 使用 OpenAI 兼容 `/v1/chat/completions` 端点（推荐）
   - `"api": "ollama"` — 使用 Ollama 原生 `/api/chat` 端点

5. **多机部署**：如果 DeepSeek 运行在另一台机器上，将 `baseUrl` 中的 `127.0.0.1` 替换为该机器的 IP 地址，并确保防火墙允许对应端口的访问。

## 故障排查

```bash
# 检查 OpenClaw 状态
openclaw status

# 运行诊断
openclaw doctor

# 查看日志
openclaw logs

# 检查 Ollama 模型列表
curl http://localhost:11434/api/tags

# 测试 DeepSeek API 连通性
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-r1:14b", "messages": [{"role": "user", "content": "Hello"}]}'
```

## 参考链接

- [OpenClaw 官方文档](https://openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [Ollama 官网](https://ollama.com)
- [DeepSeek 官网](https://deepseek.com)
- [Ollama OpenClaw 集成文档](https://docs.ollama.com/integrations/openclaw)
