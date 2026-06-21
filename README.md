# somnyx — System Dashboard

> Real-time system monitoring dashboard with FastAPI + WebSocket streaming.

**¿Para quién?** Para developers que quieren monitorear CPU, RAM, disco, red, procesos y workspace en tiempo real desde el navegador, con WebSocket push cada 2 segundos.

## Quickstart

```bash
pip install -r requirements.txt
python main.py
```

Abre `http://127.0.0.1:8080` — los datos se actualizan solos vía WebSocket.

## Stack

- **Backend**: Python · FastAPI · WebSocket · Uvicorn
- **Frontend**: HTML + CSS (dark theme) · Vanilla JS
- **Datasource**: `/proc`, `du`, `df`, `ps`, `ip`, `fd` (Linux)

## Features

- CPU, RAM, swap, disk gauges with color thresholds
- Real-time network interface status
- Top processes by CPU usage
- Workspace directory sizes (somnyx, archive, vault, notes, inbox)
- Journal status tracking
- Active git projects overview
- Keyboard shortcuts: `r` refresh, `?` help

## Proyectos relacionados

- [somnyx-tui](https://github.com/Dreamcoder08/somnyx-tui) — Terminal UI companion in Rust
- [Dreamcoder08](https://github.com/Dreamcoder08) — Profile
