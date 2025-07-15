# main.py
import contextlib

import uvicorn
from fastapi import FastAPI

from mcp_servers import echo_server, math_server, filesystem_not_safe_server


# Create a combined lifespan to manage both session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(echo_server.mcp.session_manager.run())
        await stack.enter_async_context(math_server.mcp.session_manager.run())
        await stack.enter_async_context(filesystem_not_safe_server.mcp.session_manager.run())
        yield


app = FastAPI(lifespan=lifespan)
app.mount("/echo", echo_server.mcp.streamable_http_app())
app.mount("/filesystem", filesystem_not_safe_server.mcp.streamable_http_app())
app.mount("/math", math_server.mcp.streamable_http_app())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)