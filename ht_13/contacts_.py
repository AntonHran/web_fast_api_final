import os.path
import sys
import time
from ipaddress import ip_address
from typing import Callable

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from src.database.database_ import get_db
from src.routes import contacts, auth, users
from src.conf.config import settings


app = FastAPI()


@app.on_event("startup")
async def startup():
    red = await redis.Redis(host=settings.redis_host, port=settings.redis_port,
                            db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(red)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

ALLOWED_IPS = [ip_address('192.168.1.0'), ip_address('172.16.0.0'), ip_address("127.0.0.1")]


@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    ip = ip_address(request.client.host)
    if ip not in ALLOWED_IPS:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response


@app.middleware("http")
async def custom_middleware(request: Request, call_next: Callable):
    start = time.time()
    try:
        response = await call_next(request)
    except SQLAlchemyError as error:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(error)})
    duration = time.time() - start
    response.headers["performance"] = str(duration)
    return response


@app.get("/")
async def root():
    return {"message": "Here your contacts!"}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if not result:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to yhe database")


app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


if __name__ == '__main__':
    uvicorn.run("contacts_:app", reload=True)
