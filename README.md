# nonebot-plugin-ayasanko-status

[English](README_EN.md) | [简体中文](README.md)

基于 NoneBot2 的系统运行健康度与性能状态监控插件。

---

## 特性

- **系统负载监控**：实时采集 CPU、内存、GPU 等系统硬件占用率（依赖 `psutil`）。
- **网络延迟检测**：支持检测目标服务器的网络往返延迟（依赖 `ping3`）。
- **运行时长与环境信息**：展示 NoneBot2 框架版本、Python 版本、操作系统平台及适配器列表。
- **跨插件状态联动**：可选联动 `manager_plugin` 与 `chat_plugin` 展示当前黑白名单及上下文会话数。

---

## 安装

```bash
# 使用 nb-cli
nb plugin install nonebot-plugin-ayasanko-status

# 使用 pip (完整功能)
pip install "nonebot-plugin-ayasanko-status[all]"
```

---

## 指令

| 指令 | 说明 |
| :--- | :--- |
| `/status` | 查询机器人运行状态、系统负载与适配器信息 |

---

## 开源协议

本项目采用 [MIT License](LICENSE) 许可协议。
