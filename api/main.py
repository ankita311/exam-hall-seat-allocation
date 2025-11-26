from fastapi import FastAPI

from api.routers import classes, room, allocation

app = FastAPI()

# Create data directories if they don't exist




app.include_router(classes.router)
app.include_router(room.router)
app.include_router(allocation.router)