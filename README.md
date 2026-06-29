# SOMNYX Web Dashboard

> Real-time system monitoring dashboard — FastAPI + WebSocket streaming under the Somnus × Nyx identity.

A lightweight web dashboard by Dreamcoder08 that streams system statistics to connected clients in real time via WebSocket, with a static HTML frontend and REST API fallback.

---

## Quickstart

```bash
cd somnyx-web
python3 main.py
```

**App available at:** `http://localhost:8080`

---

## Architecture

A simple FastAPI server serves a static frontend and maintains a WebSocket connection manager. Every 2 seconds, system statistics are broadcast to all connected clients.

```
somnyx-web/
├── main.py          # FastAPI server, WebSocket manager, broadcaster
├── data.py          # System stats collection
├── static/
│   └── index.html   # Frontend dashboard (HTML/CSS/JS)
```

---

## Tech Stack

| Layer | Tech | Purpose |
|-------|------|---------|
| Server | FastAPI + Uvicorn | Async HTTP and WebSocket server |
| Frontend | Vanilla HTML/CSS/JS | Lightweight dashboard UI |
| Real-time | WebSocket | Live stat streaming to clients |
| Language | Python 3 | System data collection |

---

## Scripts

| Command | Description |
|---------|-------------|
| `python3 main.py` | Start the dashboard server on `:8080` |

---

## Project Status

**Status:** Active

---

## License

MIT

---

## SDD

This project sits within the [Dreamcoder08](https://github.com/Dreamcoder08) ecosystem. Documentation is maintained in the [SDD Maestro](../arkelythex/sdd/ecosystem-readme-sdd/00-README.md).
