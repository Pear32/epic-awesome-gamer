# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from pathlib import Path

# === 引入所需库 ===
from hcaptcha_challenger.agent import AgentConfig
from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

# --- 核心路径定义 ---
PROJECT_ROOT = Path(__file__).parent
VOLUMES_DIR = PROJECT_ROOT.joinpath("volumes")
LOG_DIR = VOLUMES_DIR.joinpath("logs")
USER_DATA_DIR = VOLUMES_DIR.joinpath("user_data")
RUNTIME_DIR = VOLUMES_DIR.joinpath("runtime")
SCREENSHOTS_DIR = VOLUMES_DIR.joinpath("screenshots")
RECORD_DIR = VOLUMES_DIR.joinpath("record")
HCAPTCHA_DIR = VOLUMES_DIR.joinpath("hcaptcha")

# === 配置类定义 ===
class EpicSettings(AgentConfig):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # [修复1] 类型必须是 SecretStr，防止 AttributeError
    GEMINI_API_KEY: SecretStr | None = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY"),
        description="AiHubMix 的令牌",
    )
    
    # [修复2] 这里的 URL 会被下方的补丁自动处理，填官网地址即可
    GEMINI_BASE_URL: str = Field(
        default=os.getenv("GEMINI_BASE_URL", "https://aihubmix.com"),
        description="中转地址",
    )
    
    GEMINI_MODEL: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        description="模型名称",
    )

    EPIC_EMAIL: str = Field(default_factory=lambda: os.getenv("EPIC_EMAIL"))
    EPIC_PASSWORD: SecretStr = Field(default_factory=lambda: os.getenv("EPIC_PASSWORD"))
    DISABLE_BEZIER_TRAJECTORY: bool = Field(default=True)

    cache_dir: Path = HCAPTCHA_DIR.joinpath(".cache")
    challenge_dir: Path = HCAPTCHA_DIR.joinpath(".challenge")
    captcha_response_dir: Path = HCAPTCHA_DIR.joinpath(".captcha")

    ENABLE_APSCHEDULER: bool = Field(default=True)
    TASK_TIMEOUT_SECONDS: int = Field(default=900)
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    CELERY_WORKER_CONCURRENCY: int = Field(default=1)
    CELERY_TASK_TIME_LIMIT: int = Field(default=1200)
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=900)

    @property
    def user_data_dir(self) -> Path:
        target_ = USER_DATA_DIR.joinpath(self.EPIC_EMAIL)
        target_.mkdir(parents=True, exist_ok=True)
        return target_

settings = EpicSettings()
settings.ignore_request_questions = ["Please drag the crossing to complete the lines"]

# ==========================================
# [关键修复] AiHubMix 终极补丁 (直接集成在配置加载时)
# ==========================================
def _apply_aihubmix_patch():
    """自动应用补丁：1.修复路径 2.绕过文件上传"""
    if not settings.GEMINI_API_KEY:
        return

    try:
        # 尝试导入 google.genai，如果环境没安装也不会报错崩坏
        try:
            from google import genai
            from google.genai import types
            from google.genai._common import _contents_to_list
        except ImportError:
            print("Warning: google-genai library not found, patch skipped.")
            return

        # --- 补丁1：劫持 Client 初始化，注入中转地址 ---
        orig_init = genai.Client.__init__
        def new_init(self, *args, **kwargs):
            # 自动解密 Key
            if hasattr(settings.GEMINI_API_KEY, 'get_secret_value'):
                api_key = settings.GEMINI_API_KEY.get_secret_value()
            else:
                api_key = str(settings.GEMINI_API_KEY)
            
            kwargs['api_key'] = api_key
            
            # 智能路径修正
            base_url = settings.GEMINI_BASE_URL.rstrip('/')
            if base_url.endswith('/v1'): base_url = base_url[:-3]
            if not base_url.endswith('/gemini'): base_url = f"{base_url}/gemini"
            
            kwargs['http_options'] = types.HttpOptions(base_url=base_url)
            print(f"🚀 AiHubMix Patch Active | Model: {settings.GEMINI_MODEL} | URL: {base_url}")
            orig_init(self, *args, **kwargs)
        genai.Client.__init__ = new_init

        # --- 补丁2：劫持文件上传，改用 Base64 (绕过 400 错误) ---
        file_cache = {}

        async def patched_upload(self_files, file, **kwargs):
            # 读取文件内容
            if hasattr(file, 'read'): content = file.read()
            elif isinstance(file, (str, Path)):
                with open(file, 'rb') as f: content = f.read()
            else: content = bytes(file)
            
            if asyncio.iscoroutine(content): content = await content
            
            # 存入缓存，不发请求
            file_id = f"bypass_{id(content)}"
            file_cache[file_id] = content
            return types.File(name=file_id, uri=file_id, mime_type="image/png")

        orig_generate = genai.models.AsyncModels.generate_content
        async def patched_generate(self_models, model, contents, **kwargs):
            normalized = _contents_to_list(contents)
            for content in normalized:
                for i, part in enumerate(content.parts):
                    # 将伪造的文件 ID 替换为真实的 Base64 数据
                    if part.file_data and part.file_data.file_uri in file_cache:
                        data = file_cache[part.file_data.file_uri]
                        content.parts[i] = types.Part.from_bytes(data=data, mime_type="image/png")
            return await orig_generate(self_models, model, normalized, **kwargs)

        genai.files.AsyncFiles.upload = patched_upload
        genai.models.AsyncModels.generate_content = patched_generate

    except Exception as e:
        print(f"❌ Patch failed: {e}")

# 立即执行补丁
_apply_aihubmix_patch()
