import os
import sys
import time
# from ipaddress import ip_address
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

from ht_13.src.database.database_ import get_db
from ht_13.src.routes import contacts, auth, users
from ht_13.src.conf.config import settings


app = FastAPI()


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are used by the app, such as caches or databases.

    :return: The fastapilimiter instance
    :doc-author: Trelent
    """
    red = await redis.Redis(host=settings.redis_host, port=settings.redis_port,
                            db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(red)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

'''ALLOWED_IPS = [ip_address('192.168.1.0'), ip_address('172.16.0.0'), ip_address("127.0.0.1")]


@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    """
    The limit_access_by_ip function is a middleware function that limits access to the API by IP address.
    It checks if the client's IP address is in ALLOWED_IPS, and if not, returns a 403 Forbidden response.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the next function in the pipeline
    :return: A jsonresponse object with a status code of 403
    :doc-author: Trelent
    """
    ip = ip_address(request.client.host)
    if ip not in ALLOWED_IPS:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response'''


@app.middleware("http")
async def custom_middleware(request: Request, call_next: Callable):
    """
    The custom_middleware function is a middleware function that will be called before the request
    is passed to the route handler. It will catch any SQLAlchemy errors and return them as JSON responses,
    and it will add a performance header to every response.

    :param request: Request: Access the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: A response object
    :doc-author: Trelent
    """
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
    """
    The root function is a simple HTTP endpoint that returns a JSON object
    containing the message &quot;Here your contacts!&quot;.

    :return: A dict, so we can use the json() middleware
    :doc-author: Trelent
    """
    return {"message": "Here your contacts!"}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks the database connection.
    It returns a JSON object with the message &quot;Welcome to FastAPI&quot; if everything is working correctly.

    :param db: Session: Get the database session from the dependency
    :return: A dictionary with a message
    :doc-author: Trelent
    """
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
