import os
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse

app = FastAPI(title="HTTP+SSE MCP Server")
security = HTTPBearer()

# 12-Тапсырма: Қауіпсіздік үшін Bearer Токен бекітеміз
BEARER_TOKEN = "my_secret_mcp_token_2026"

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Рұқсат жоқ! Токен қате."
        )
    return credentials.credentials

@app.get("/mcp/status")
async def get_status(token: str = Depends(verify_token)):
    """Бот осы endpoint арқылы Docker-дегі сервердің күйін тексереді"""
    return {
        "status": "Бетпе-бет байланыс орнатылды! Бұл мәлімет Docker-дегі HTTP/SSE серверінен Bearer токен валидациясынан өтіп алынды. [SSE Reconnection OK]"
    }

# SSE (Server-Sent Events) арқылы үздіксіз байланыс ағыны
@app.get("/mcp/sse")
async def sse_endpoint(token: str = Depends(verify_token)):
    async def event_generator():
        while True:
            yield "data: {\"event\": \"ping\", \"status\": \"connected\"}\n\n"
            await asyncio.sleep(5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)