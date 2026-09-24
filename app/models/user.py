from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    plan = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bot_config = relationship("BotConfig", back_populates="user", uselist=False)
    channel_configs = relationship("ChannelConfig", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class BotConfig(Base):
    __tablename__ = "bot_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String, default="شركتي")
    system_prompt = Column(Text, default="You are a helpful AI assistant for customer service.")
    tone = Column(String, default="professional")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="bot_config")

class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel_type = Column(String, index=True) # 'whatsapp', 'messenger'
    provider_id = Column(String) # e.g. Phone number ID or Page ID
    access_token = Column(String)
    verify_token = Column(String) # For webhooks
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="channel_configs")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    channel_type = Column(String)
    customer_id = Column(String) # phone number or messenger PSID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender = Column(String) # 'customer' or 'bot' or 'agent'
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
