# EPIC 免费人 (AiHubMix 增强版)

<div align="center">
<p>🍷 优雅地自动领取 Epic Store 每周免费游戏。</p>
<img src="[https://img.shields.io/static/v1?message=Python](https://www.google.com/search?q=https://img.shields.io/static/v1%3Fmessage%3DPython) 3.12&color=blue&style=for-the-badge&logo=python&label=Build">
<img src="[https://img.shields.io/github/license/QIN2DIM/epic-awesome-gamer?style=for-the-badge](https://img.shields.io/github/license/QIN2DIM/epic-awesome-gamer?style=for-the-badge)">
<img src="[https://img.shields.io/github/actions/workflow/status/QIN2DIM/epic-awesome-gamer/ci.yaml?label=Auto](https://www.google.com/search?q=https://img.shields.io/github/actions/workflow/status/QIN2DIM/epic-awesome-gamer/ci.yaml%3Flabel%3DAuto) Claim&style=for-the-badge">
</div>

## 📖 项目简介

**Epic 免费人** 是一款全自动的 Epic Games Store 免费游戏领取工具。

本项目在原版基础上进行了**深度改造**，专为 **GitHub Actions** 环境优化，并集成了 **AiHubMix (Gemini)** 模型，能够利用 AI 视觉能力轻松通过复杂的 hCaptcha 人机验证。

## ✨ 核心特性

* **🤖 AI 强力过验证**：内置针对 `google-genai` SDK 的底层补丁，支持通过 **AiHubMix** 等中转站调用 Gemini Pro Vision 模型，完美处理 hCaptcha 旋转/点击验证码。
* **🛒 全流程覆盖**：
* 支持标准的 **"加入购物车 -> 结账"** 流程。
* **[新增]** 支持 **"即时结账 (Instant Checkout)"** 流程（针对 *Blood West* 等直接点击 "Get" 的游戏）。
* **[新增]** 自动处理 **"内容警告 (Content Warning)"** 弹窗。
* **[新增]** 不再跳过捆绑包 (Bundles)，所有免费内容一网打尽。


* **☁️ 云端自动运行**：深度适配 GitHub Actions，无需本地挂机，每周定时自动领取。
* **⚡️ 极速环境**：使用 `uv` 进行依赖管理，部署速度极快。

## 🚀 部署指南 (GitHub Actions)

这是最推荐的部署方式，完全免费且无需维护服务器。

### 1. Fork 本仓库

点击右上角的 **Fork** 按钮，将本项目复制到你的 GitHub 账号下。

### 2. 配置 Secrets

进入你 Fork 后的仓库，点击 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，添加以下变量：

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `EPIC_EMAIL` | ✅ | 你的 Epic 游戏账号邮箱。<br>

<br>⚠️ **必须关闭二步验证 (2FA)**。 |
| `EPIC_PASSWORD` | ✅ | 你的 Epic 游戏密码。 |
| `GEMINI_API_KEY` | ✅ | AiHubMix 或 Google AI Studio 的 API Key (以 `sk-` 开头)。 |
| `GEMINI_BASE_URL` | ❌ | **中转接口地址**。<br>

<br>默认为 `https://aihubmix.com/v1`，如使用官方接口可填 `https://generativelanguage.googleapis.com`。 |
| `GEMINI_MODEL` | ❌ | **模型名称**。<br>

<br>默认为 `gemini-2.5-pro` (推荐)，也可尝试 `gemini-1.5-pro`。 |

> **关于 AiHubMix 配置**：
> 本项目已内置 `utils.py` 补丁，能够自动处理中转站的文件上传限制（自动转换为 Base64），你只需填入 Key 和 URL 即可，无需担心 400/403 报错。

### 3. 启用工作流

1. 点击仓库上方的 **Actions** 标签页。
2. 如果看到警告 "Workflows aren't being run on this forked repository"，点击绿色按钮 **I understand my workflows, go ahead and enable them**。
3. 选择左侧的 `Epic Free Games` (或类似名称的工作流)。
4. 点击右侧的 **Run workflow** 手动触发一次测试。

之后，脚本将根据 `.github/workflows` 中的配置（通常为每周）自动运行。

---

## 🐳 其他部署方式 (Docker)

如果你拥有自己的服务器（VPS/NAS），也可以使用 Docker 部署。

```bash
# 1. 下载代码
git clone https://github.com/your-username/epic-awesome-gamer.git
cd epic-awesome-gamer

# 2. 配置环境变量
cp docker/.env.example .env
# 编辑 .env 文件填入上述账号和 Key 信息

# 3. 启动容器
docker compose -f docker/docker-compose.yaml up -d

```

---

## 🛠️ 常见问题 (FAQ)

**Q: 为什么日志显示 "Login with Email ... Timeout"?**
A: 这是因为 GitHub Actions 的共享 IP 可能被 Epic 临时风控。通常情况下，GitHub 会自动重试，或者你可以等待几小时后手动重试，更换 IP 后即可成功。

**Q: 需要关闭二步验证 (2FA) 吗？**
A: **必须关闭**。由于脚本运行在无头模式下，无法处理短信或邮件验证码。请确保账号已关闭 2FA。

**Q: 为什么有的游戏显示 "Instant Checkout"?**
A: 部分游戏（如 *Blood West*）点击 "Get" 后不会进入购物车，而是直接弹出支付窗口。本项目已针对此逻辑进行了专门适配，能够自动识别并完成点击。

**Q: 使用中转站 API 报错 "400 Bad Request" 或 "File API not supported"?**
A: 请确保你使用的是本仓库最新代码。`utils.py` 中包含了 `patch_aihubmix` 补丁，它会拦截 Google SDK 的原生文件上传行为，将其转换为 Inline Base64 数据，从而完美绕过中转站的限制。

---

## ⚠️ 免责声明

本项目仅供学习交流使用。

1. 使用脚本领取游戏可能违反 Epic Games 的服务条款，请自行承担风险。
2. 请勿将本项目用于商业用途。
3. 开发者不对因使用本项目导致的账号封禁或其他损失负责。
