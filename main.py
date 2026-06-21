#!/usr/bin/env python3
# main.py — SOMNYX Web Dashboard | dreamcoder08
# FastAPI + WebSocket + HTML/CSS/JS | 2026

import asyncio, json, webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import data

app = FastAPI(title="SOMNYX", docs_url=None, redoc_url=None)

STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

# ── REST ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return (STATIC / "index.html").read_text()

@app.get("/api/stats")
async def stats():
    return data.full_stats()

# ── WebSocket: streaming en tiempo real ───────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(ws)

async def broadcaster():
    """Envia stats a todos los clientes conectados cada 2 segundos."""
    while True:
        await asyncio.sleep(2)
        if manager.active:
            try:
                payload = data.full_stats()
                await manager.broadcast(payload)
            except Exception:
                pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcaster())

# ── Entry point ───────────────────────────────────────────────────────────────

def serve(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
    print(f"\n  SOMNYX Web Dashboard")
    print(f"  dreamcoder08 | Somnus × Nyx")
    print(f"  → http://{host}:{port}\n")
    if open_browser:
        import threading
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    serve()
