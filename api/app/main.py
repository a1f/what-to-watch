from typing import Annotated, Final

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import Engine

from api.app.db import check_connection, get_engine

app: Final[FastAPI] = FastAPI(title="What to Watch API")


@app.get("/health")
def health(engine: Annotated[Engine, Depends(get_engine)]) -> JSONResponse:
    database_up: bool = check_connection(engine)
    payload: dict[str, str] = {
        "status": "ok" if database_up else "degraded",
        "database": "up" if database_up else "down",
    }
    return JSONResponse(status_code=200 if database_up else 503, content=payload)
