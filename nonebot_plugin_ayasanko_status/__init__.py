# fmt: off
from __future__ import annotations

import datetime
import platform
import sys
import time
from typing import cast
from types import ModuleType

import nonebot
from nonebot import get_adapters, get_driver, on_command, require
from nonebot.adapters import Bot, Event
from nonebot.log import logger

# ---------- 可选依赖 ----------
# 用小写前缀变量避免 reportConstantRedefinition（全大写视为常量，不可在 except 中重赋值）
_psutil_available: bool
_ping3_available: bool

try:
    import psutil  # type: ignore[import-untyped]
    _psutil_available = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    _psutil_available = False
    logger.warning("psutil 未安装，CPU/内存信息将不可用")

try:
    from ping3 import ping  # type: ignore[import-untyped, import-not-found] # pyright: ignore[reportUnknownVariableType]
    _ping3_available = True
except ImportError:
    ping = None  # type: ignore[assignment]
    _ping3_available = False
    logger.warning("ping3 未安装，PING 信息将不可用")

# ---------- 跨插件依赖 ----------
_manager_module: ModuleType | None = None
try:
    _manager_module = require("nonebot_plugin_ayasanko_manager")  # type: ignore[assignment]
    logger.info("成功连接到 nonebot_plugin_ayasanko_manager")
except Exception:
    try:
        _manager_module = require("manager_plugin")  # type: ignore[assignment]
        logger.info("成功连接到 manager_plugin")
    except Exception:
        logger.warning("无法连接到 manager_plugin，管理器配置信息将不可用")

_chat_module: ModuleType | None = None
try:
    _chat_module = require("nonebot_plugin_ayasanko_chat")  # type: ignore[assignment]
    logger.info("成功连接到 nonebot_plugin_ayasanko_chat")
except Exception:
    try:
        _chat_module = require("chat_plugin")  # type: ignore[assignment]
        logger.info("成功连接到 chat_plugin")
    except Exception:
        logger.warning("无法连接到 chat_plugin，上下文信息将不可用")

def _get_manager_config() -> object | None:
    """安全获取 manager_plugin 的配置，失败返回 None"""
    if _manager_module is None:
        return None
    get_config = getattr(_manager_module, "get_config", None)
    if callable(get_config):
        try:
            result: object = get_config()  # type: ignore[no-any-return]  # get_config 返回 Any
            return result
        except Exception as e:
            logger.error(f"获取管理器配置失败: {e}")
    return None

def _get_context_count() -> int:
    if _chat_module is None:
        return -1
    get_count = getattr(_chat_module, "get_context_count", None)
    if callable(get_count):
        try:
            result: object = get_count()  # type: ignore[no-any-return]
            return int(result) if isinstance(result, int) else -1
        except Exception:
            pass
    return -1


# ---------- 启动时间 ----------
driver = get_driver()
START_TIME = time.time()

status = on_command("/status", priority=10, block=True)


# ---------- 工具函数 ----------
def format_uptime(seconds: float) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分")
    parts.append(f"{secs}秒")
    return "".join(parts)


def get_cpu_info() -> str:
    if not _psutil_available or psutil is None:
        return "未知 (需安装 psutil)"
    try:
        cpu: object = psutil.cpu_percent(interval=0.5)
        return f"{cpu}%"
    except Exception as e:
        return f"错误: {e}"


def get_ram_info() -> str:
    if not _psutil_available or psutil is None:
        return "未知 (需安装 psutil)"
    try:
        mem: object = psutil.virtual_memory()
        # psutil 无类型 stub，用 getattr + cast 提取数值，截断 Any 传播
        used = float(cast(float, getattr(mem, "used", 0)))
        total = float(cast(float, getattr(mem, "total", 1)))
        percent = float(cast(float, getattr(mem, "percent", 0)))
        return f"{used / (1024**3):.1f}GB / {total / (1024**3):.1f}GB ({percent}%)"
    except Exception as e:
        return f"错误: {e}"


def get_gpu_info() -> str:
    try:
        from pynvml import (  # type: ignore[import-untyped, import-not-found]  # pyright: ignore[reportMissingImports]
            nvmlDeviceGetHandleByIndex,   # pyright: ignore[reportUnknownVariableType]
            nvmlDeviceGetUtilizationRates,  # pyright: ignore[reportUnknownVariableType]
            nvmlInit,   # pyright: ignore[reportUnknownVariableType]
            nvmlShutdown,  # pyright: ignore[reportUnknownVariableType]
        )
        nvmlInit()  # type: ignore[no-untyped-call]
        handle: object = cast(object, nvmlDeviceGetHandleByIndex(0))  # type: ignore[no-untyped-call]
        util: object = cast(object, nvmlDeviceGetUtilizationRates(handle))  # type: ignore[no-untyped-call]
        nvmlShutdown()  # type: ignore[no-untyped-call]
        gpu_util: object = getattr(util, "gpu", "未知")
        return f"GPU 使用率: {gpu_util}%"
    except ImportError:
        return "未知 (需安装 pynvml)"
    except Exception:
        return "未知 (无 NVIDIA 显卡或驱动问题)"


def get_ping(host: str = "www.baidu.com") -> str:
    if not _ping3_available or ping is None:
        return "未知 (需安装 ping3)"
    try:
        rtt = cast("float | None", ping(host, timeout=2))
        if rtt is None:
            return "超时"
        return f"{rtt * 1000:.2f}ms"
    except Exception as e:
        return f"错误: {e}"


def get_adapter_info() -> list[str]:
    adapters = get_adapters()
    info: list[str] = []
    for name, adapter_cls in adapters.items():
        version: object = (
            getattr(adapter_cls, "get_version", None) or
            getattr(adapter_cls, "version", "未知")
        )
        if callable(version):
            version = version()
        info.append(f"{name} (版本: {version})")
    return info

# ---------- 状态处理 ----------
@status.handle()
async def handle_status(bot: Bot, event: Event) -> None:
    uptime = format_uptime(time.time() - START_TIME)
    cpu = get_cpu_info()
    ram = get_ram_info()
    gpu = get_gpu_info()
    ping_result = get_ping()

    ctx_count = _get_context_count()
    ctx_text = f"{ctx_count} 人" if ctx_count >= 0 else "(不可用)"

    nb_version: str = getattr(nonebot, "__version__", "未知")
    python_version = sys.version.split()[0]
    os_info = platform.platform()

    group_id: object = getattr(event, "group_id", None)
    current_target = (
        f"群聊 {group_id}" if group_id is not None
        else f"好友 {event.get_user_id()}"
    )

    # 管理器配置
    whitelist_groups: list[int] = []
    blacklist_users: list[int] = []
    allowed_commands: list[str] = []
    cfg = _get_manager_config()
    if cfg is not None:
        raw_wl: object = getattr(cfg, "group_whitelist", [])
        raw_bl: object = getattr(cfg, "user_blacklist", [])
        raw_cmd: object = getattr(cfg, "commands", [])
        # cast(list[object], ...) 截断 Unknown/Any，再用 isinstance 过滤元素类型
        if isinstance(raw_wl, list):
            whitelist_groups = [x for x in cast(list[object], raw_wl) if isinstance(x, int)]
        if isinstance(raw_bl, list):
            blacklist_users = [x for x in cast(list[object], raw_bl) if isinstance(x, int)]
        if isinstance(raw_cmd, list):
            allowed_commands = [x for x in cast(list[object], raw_cmd) if isinstance(x, str)]

    adapters_info = get_adapter_info()
    lines: list[str] = [
        "机器人状态报告",
        "=" * 10,
        f"查询时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "• 基本信息",
        f"   • QQ号: {bot.self_id}",
        f"   • 运行时长: {uptime}",
        f"   • CPU使用率: {cpu}",
        f"   • 内存使用: {ram}",
        f"   • GPU状态: {gpu}",
        f"   • PING(百度): {ping_result}",
        "",
        "• 版本信息",
        f"   • NoneBot框架: v{nb_version}",
        f"   • Python: {python_version}",
        f"   • 操作系统: {os_info}",
        *[f"   • 协议端{i}: {line}" for i, line in enumerate(adapters_info, 1)],
        "",
        "• 当前会话",
        f"   • {current_target}",
        f"   • Chat_Plugin人格数: {ctx_text}",
        "",
        "• 管理器配置",
        f"   • 白名单群聊: {', '.join(map(str, whitelist_groups)) or 'None'}",
        f"   • 黑名单好友: {', '.join(map(str, blacklist_users)) or 'None'}",
        f"   • 白名单指令: {', '.join(allowed_commands) or 'None'}",
    ]

    await bot.send(event, "\n".join(lines))  # pyright: ignore[reportUnknownMemberType]
