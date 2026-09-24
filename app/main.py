from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsAuto API")

from fastapi.responses import JSONResponse
import traceback

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)}
    )

from app.api import auth, webhooks, settings, channels

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])


@app.get("/")
def root():
    return {"message": "WhatsAuto API is running"}
