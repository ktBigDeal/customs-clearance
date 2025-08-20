#!/usr/bin/env python3
"""
테스트용 간단한 FastAPI 앱
"""

from fastapi import FastAPI
import os

app = FastAPI(title="Simple Test App")

@app.get("/")
async def root():
    return {"message": "Hello World", "port": os.getenv("PORT", "8080")}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)