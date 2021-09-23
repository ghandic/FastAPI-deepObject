# FastAPI - deepObject

An example of implementation for deep object encoding for url query parameters in FastAPI

## Proposed usage

To allow deepObjects as defined in [Swagger spec](https://swagger.io/docs/specification/serialization/#query) we can remap using alias's on the Query. For example in the below we have a `User` which has a role and a first_name, this would have the url string encoded as `"/<endpoint>?user[role]=admin&user[first_name]=Alex"`, using the proposed solution it handles single level nesting of objects, optional objects and list of objects in the query string. This would then give you access to the `User` object without additional effort for parsing and validation.

```python
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, DeepQuery # NOTE: This is proposed usage, see custom.py for implementation

from models import User, UserWithEnum
# from custom import DeepQuery


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
```
