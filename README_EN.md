# nonebot-plugin-ayasanko-status

[English](README_EN.md) | [简体中文](README.md)

NoneBot2 system health and running status inspection plugin.

---

## Features

- **System Resource Monitoring**: Inspects CPU, Memory, and GPU utilization (requires `psutil`).
- **Network Latency Check**: Measures network RTT to target endpoints (requires `ping3`).
- **Runtime Diagnostics**: Displays NoneBot2 version, Python runtime, operating system, and loaded protocol adapters.
- **Inter-Plugin Compatibility**: Dynamically integrates with `manager_plugin` and `chat_plugin` to report blacklist/whitelist states and active conversation contexts.

---

## Installation

```bash
# via nb-cli
nb plugin install nonebot-plugin-ayasanko-status

# via pip (all optional features)
pip install "nonebot-plugin-ayasanko-status[all]"
```

---

## Commands

| Command | Description |
| :--- | :--- |
| `/status` | View system resource metrics, runtime details, and adapter states |

---

## License

This project is licensed under the [MIT License](LICENSE).
