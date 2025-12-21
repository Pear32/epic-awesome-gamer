# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import sys
from zoneinfo import ZoneInfo
from loguru import logger
from settings import settings

def timezone_filter(record):
    record["time"] = record["time"].astimezone(ZoneInfo("Asia/Shanghai"))
    return record

def patch_aihubmix():
    """精简版拦截器：完美适配 Gemini 原生协议中转"""
    if not settings.GEMINI_API_KEY:
        return
    
    try:
        from google import genai
        from google.genai import types
        
        orig_init = genai.Client.__init__
        
        def new_init(self, *args, **kwargs):
            # 获取明文 Key
            api_key = settings.GEMINI_API_KEY.get_secret_value()
            kwargs['api_key'] = api_key
            
            # 处理 Base URL：确保它是纯净的域名，不带 /v1 路径
            base_url = settings.GEMINI_BASE_URL.rstrip('/')
            if base_url.endswith('/v1'):
                base_url = base_url[:-3]
            
            # 注入配置
            kwargs['http_options'] = types.HttpOptions(base_url=base_url)
            logger.info(f"🚀 AiHubMix 拦截成功 | 模型: {settings.GEMINI_MODEL} | 地址: {base_url}")
            orig_init(self, *args, **kwargs)
            
        genai.Client.__init__ = new_init
    except Exception as e:
        logger.error(f"拦截器加载失败: {e}")

def init_log(**sink_channel):
    patch_aihubmix()
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logger.remove()
    logger.add(sink=sys.stdout, level=log_level, filter=timezone_filter)
    return logger

init_log()
