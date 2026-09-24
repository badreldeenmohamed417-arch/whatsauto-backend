from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsAuto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, webhooks

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])


@app.get("/")
def root():
    return {"message": "WhatsAuto API is running"}
