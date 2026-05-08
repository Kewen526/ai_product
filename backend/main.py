import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import UPLOAD_DIR
from database import Base, engine
from routers import auth, images, tags

# Create application tables (daily_image_pool, image_tags) if they don't exist
Base.metadata.create_all(bind=engine)

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Product Image Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve extracted ZIP images as static files
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(images.router)
app.include_router(tags.router)


@app.get("/health")
def health():
    return {"status": "ok"}
