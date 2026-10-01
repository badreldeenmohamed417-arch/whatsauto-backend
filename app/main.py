from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from app.db.session import engine, Base
from app.models import user  # Register all SQLAlchemy models

# create_all creates missing tables, but does not alter existing tables.
Base.metadata.create_all(bind=engine)

# Production safety net: older databases may predate the subscription migration.
# This is intentionally idempotent and only adds columns that are missing.
def ensure_schema_compatibility():
    required_columns = {
        "users": {
            "subscription_status": "VARCHAR DEFAULT 'EXPIRED'",
            "expires_at": "TIMESTAMP WITH TIME ZONE",
        },
        "bot_configs": {
            "description": "TEXT DEFAULT ''",
            "products": "TEXT DEFAULT ''",
            "instructions": "TEXT DEFAULT ''",
            "handover_number": "VARCHAR DEFAULT ''",
        },
        "conversations": {
            "customer_name": "VARCHAR DEFAULT ''",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table, columns in required_columns.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(
                        f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'
                    ))

ensure_schema_compatibility()

app = FastAPI(title="WhatsAuto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled request error: {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

from app.api import auth, webhooks, settings, channels, admin, chats

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])

@app.get("/")
def root():
    return {"message": "WhatsAuto API is running"}
