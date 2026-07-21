# Third-Party Music API Integration

## Context

When a user wants to integrate a private music generation API (e.g., 云五音乐 / YunWu Music) and provides an Apifox or internal documentation URL, the agent typically cannot access it due to auth walls or network restrictions.

## Workflow

1. **Acknowledge the limitation** — state clearly that the URL is private/auth-protected and you cannot access it directly.
2. **Request the docs in a transferable format** — ask the user to:
   - Take a screenshot of the API docs page
   - Copy-paste the endpoint details (URL, method, headers, body, response)
3. **Do not guess parameters** — never fabricate request schemas or auth tokens.
4. **Once docs are received**, write a typed client module with:
   - Base URL configuration
   - Auth header injection
   - Request/response Pydantic models (Python) or Zod schemas (Node.js)
   - Retry logic and timeout handling
   - Streaming response support if applicable

## Example: Generic Music API Client (Python)

```python
import os
import httpx
from typing import Optional, BinaryIO
from pydantic import BaseModel

class MusicGenerationRequest(BaseModel):
    prompt: str
    duration: Optional[int] = 30
    style: Optional[str] = "pop"

class MusicGenerationResponse(BaseModel):
    task_id: str
    status: str
    audio_url: Optional[str] = None

class MusicAPIClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def generate(self, req: MusicGenerationRequest) -> MusicGenerationResponse:
        resp = await self.client.post(f"{self.base_url}/v1/music/generate", json=req.dict())
        resp.raise_for_status()
        return MusicGenerationResponse(**resp.json())

    async def poll(self, task_id: str, interval: float = 2.0) -> MusicGenerationResponse:
        while True:
            resp = await self.client.get(f"{self.base_url}/v1/music/status/{task_id}")
            resp.raise_for_status()
            data = MusicGenerationResponse(**resp.json())
            if data.status in ("done", "failed"):
                return data
            await asyncio.sleep(interval)

    async def download(self, audio_url: str, output_path: str):
        async with self.client.stream("GET", audio_url) as resp:
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
```

## Pitfalls

- **Async vs sync**: Music generation APIs are often async (return task_id, poll for result). Match the pattern.
- **Binary output**: If the API returns audio bytes directly, use `response.content` or streaming, not `.json()`.
- **Auth rotation**: Some Chinese music APIs use short-lived tokens; implement a refresh hook.
- **Rate limits**: Music generation is expensive; respect `Retry-After` headers.
