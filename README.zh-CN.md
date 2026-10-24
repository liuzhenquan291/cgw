# cgw — Claude Gateway

多环境模型网关，让 Claude Desktop 通过本地代理使用第三方 LLM 服务（MiMo、DeepSeek、Qwen 等）。一条命令或一次点击即可切换服务商。

[English](README.md)

## 功能特性

- **多环境管理** — 配置多个 LLM 服务商，即时切换
- **模型映射** — 将 Claude 风格模型 ID 映射到任意上游模型
- **Web 管理界面** — 在浏览器中管理环境、模型和 Claude Desktop 集成
- **命令行工具（`cgw`）** — 在终端查看状态、切换环境、管理网关
- **Claude Desktop 集成** — 一键同步和重启第三方推理配置
- **热加载** — 模型变更即时生效，无需重启网关

## 架构

```
Claude Desktop
    │  （Claude 风格模型 ID）
    ▼
本地网关 (cgw)
    │  （重写模型名，路由到当前激活环境）
    ▼
第三方 LLM API（MiMo、DeepSeek、Qwen 等）
```

## 快速开始

```bash
git clone <repo-url> && cd claude_desktop_gateway
./install.sh
```

安装脚本会：
1. 创建 Python 虚拟环境并安装依赖
2. 引导配置第一个服务商（API Key、上游 URL）
3. 将 `cgw` 命令安装到 PATH
4. 启动网关

然后打开 **http://127.0.0.1:8787/admin** 在浏览器中管理所有配置。

## cgw 命令

```bash
cgw status              # 查看网关和环境状态
cgw profiles            # 列出所有环境
cgw active              # 显示当前激活环境
cgw switch <name>       # 切换到指定环境
cgw add                 # 交互式添加新环境
cgw edit <name>         # 编辑环境
cgw remove <name>       # 删除环境
cgw start               # 启动网关
cgw stop                # 停止网关
cgw restart             # 重启网关
cgw web                 # 打开 Web 管理页面
cgw logs                # 查看网关日志
```

## Makefile 命令

```bash
make install            # 一键安装
make start              # 启动网关
make stop               # 停止网关
make restart            # 重启网关
make status             # 查看状态
make profiles           # 列出环境
make switch PROFILE=x   # 切换环境
make web                # 打开管理页面
make logs               # 查看日志
```

## 配置说明

### 环境配置

环境配置存储在 `~/.claude-gateway/profiles.json`：

```json
{
  "version": 2,
  "active": "my-provider",
  "profiles": {
    "my-provider": {
      "upstream_url": "https://api.example.com/anthropic",
      "api_key": "your-api-key",
      "auth_scheme": "api-key",
      "models": [
        {
          "id": "claude-opus-4-6",
          "upstream": "provider-model-name",
          "display_name": "My Model"
        }
      ]
    }
  }
}
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `MIMO_API_KEY` | API 密钥（也存储在 `.env` 文件中） |

### 模型 ID 要求

Claude Desktop 会验证模型 ID，必须满足：
- 包含 `claude`、`opus`、`sonnet`、`haiku`、`fable` 或 `anthropic`
- 不匹配已知竞品名称（Claude Desktop 有黑名单机制）

使用 Claude 风格 ID（如 `claude-opus-4-6`），映射到真实的上游模型名。

## Web 管理界面

访问 `http://127.0.0.1:8787/admin`：

- **环境切换器** — 右上角徽章，点击管理环境
- **模型管理** — 添加/编辑/删除模型映射
- **Claude Desktop 同步** — 推送配置到 Desktop，带确认的重启
- **API Key 管理** — 配置服务商 API 密钥

## 项目结构

```
├── gateway.py           # FastAPI 代理服务器
├── profile_manager.py   # 多环境配置管理器
├── cli.py               # cgw 命令行工具
├── admin_page.py        # Web 管理界面（单文件 HTML）
├── desktop_sync.py      # Claude Desktop 集成
├── config_store.py      # 旧版配置存储（向后兼容）
├── install.sh           # 一键安装脚本
├── Makefile             # 构建/运行命令
└── .gitignore           # 排除敏感文件和运行时文件
```

## 环境要求

- Python 3.7+
- macOS（Claude Desktop 集成需要）
- 依赖：`fastapi`、`uvicorn`、`httpx`（自动安装）

## 许可证

MIT
