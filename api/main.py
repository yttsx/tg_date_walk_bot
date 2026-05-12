from fastapi import FastAPI

from api.routers import auth, groups, history, places, ratings, routes

app = FastAPI(title="WalkBot API", version="0.1.0")

app.include_router(auth.router)
app.include_router(places.router)
app.include_router(routes.router)
app.include_router(ratings.router)
app.include_router(history.router)
app.include_router(groups.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
