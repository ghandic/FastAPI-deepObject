from typing import Optional, List

import uvicorn
from fastapi import FastAPI

from models import User, UserWithEnum
from custom import DeepQuery


app = FastAPI(version="0.1.0", docs_url="/")


@app.get("/optional-search")
async def search(user: Optional[User] = DeepQuery(Optional[User], name="bob")):
    print(user)


@app.get("/enum-search")
async def search(user: UserWithEnum = DeepQuery(UserWithEnum, name="bob")):
    print(user)


@app.get("/search")
async def search(user: User = DeepQuery(User, name="bob")):
    print(user)


@app.get("/searchs")
async def searchs(users: List[User] = DeepQuery(List[User])):
    print(users)


if __name__ == "__main__":
    uvicorn.run("app:app", port=5555, host="0.0.0.0", reload=True, log_config=None)
