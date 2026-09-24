from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String, default="user", nullable=False)
    subscription_status = Column(String, default="EXPIRED", nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bot_config = relationship("BotConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    channel_configs = relationship("ChannelConfig", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class BotConfig(Base):
    __tablename__ = "bot_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, default="شركتي")
    description = Column(Text, default="")
    products = Column(Text, default="")
    instructions = Column(Text, default="")
    tone = Column(String, default="professional")
    handover_number = Column(String, default="")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="bot_config")

class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_type = Column(String, index=True, nullable=False)
    provider_id = Column(String, nullable=False)
    access_token = Column(Text, default="")
    verify_token = Column(String, default="")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="channel_configs")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_type = Column(String, nullable=False)
    customer_id = Column(String, nullable=False)
    customer_name = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
