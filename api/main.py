from fastapi import FastAPI

from api.routers import auth, groups, history, places, ratings, routes

# VERSION MARKER: v2-no-postgis - 2026-05-12
print("=" * 60)
print("API STARTING: v2-no-postgis (geom column removed)")
print("=" * 60)

app = FastAPI(title="WalkBot API", version="0.2.0")

app.include_router(auth.router)
app.include_router(places.router)
app.include_router(routes.router)
app.include_router(ratings.router)
app.include_router(history.router)
app.include_router(groups.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
