import os
import json
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, BotConfig, ChannelConfig, Conversation, Message
from app.services.ai import generate_response, decide_action
from app.services.crypto import decrypt_secret
from app.api.settings import subscription_active
import httpx

router = APIRouter()
VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "")

async def graph_post(access_token: str, url: str, payload: dict):
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, params={"access_token": access_token}, json=payload)
        response.raise_for_status()
        return response.json()

def parse_products(raw):
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except Exception:
        return []

def get_config_for_provider(db, channel_type: str, provider_id: str):
    return db.query(ChannelConfig).filter(
        ChannelConfig.channel_type == channel_type,
        ChannelConfig.provider_id == provider_id,
        ChannelConfig.is_active == True
    ).first()

def get_conversation(db, user_id: int, channel: str, customer_id: str, customer_name: str = ""):
    conversation = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.channel_type == channel,
        Conversation.customer_id == customer_id
    ).first()
    if not conversation:
        conversation = Conversation(
            user_id=user_id, channel_type=channel,
            customer_id=customer_id, customer_name=customer_name or ""
        )
        db.add(conversation)
        db.flush()
    elif customer_name and not conversation.customer_name:
        conversation.customer_name = customer_name
    return conversation

async def process_message(db, channel, provider_id, customer_id, text, customer_name=""):
    channel_config = get_config_for_provider(db, channel, provider_id)
    if not channel_config or not text:
        return
    user = db.query(User).filter(User.id == channel_config.user_id).first()
    if not user or not subscription_active(user):
        return
    bot = db.query(BotConfig).filter(BotConfig.user_id == user.id).first()
    if not bot or not bot.is_active:
        return

    conversation = get_conversation(db, user.id, channel, customer_id, customer_name)
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(12)
        .all()
    )
    history_text = "\n".join(f"{m.sender}: {m.content}" for m in reversed(history))
    system_prompt = f"""أنت موظف خدمة عملاء لشركة {bot.company_name}.
وصف الشركة:
{bot.description}

المنتجات والخدمات:
{bot.products}

تعليمات إضافية:
{bot.instructions}

لهجة الرد:
{bot.tone}

رقم التحويل لموظف بشري:
{bot.handover_number}

قواعد:
- رد باختصار وبوضوح.
- لا تخترع معلومات أو أسعاراً غير موجودة.
- إذا لم تعرف الإجابة، أخبر العميل أن موظفاً من الفريق يمكنه مساعدته.
- لا تدّعي تنفيذ إجراء لم تنفذه.
- حافظ على لغة العميل ولهجته قدر الإمكان.
"""
    db.add(Message(conversation_id=conversation.id, sender="customer", content=text))
    db.commit()
    action = await decide_action(
        system_prompt + "\n\nسياق المحادثة الأخير:\n" + history_text,
        text,
        channel,
        parse_products(bot.products)
    )
    if action["action"] == "ignore":
        return
    reply = action.get("reply") or await generate_response(system_prompt, text, bot.tone)
    if action["action"] == "handover" and bot.handover_number:
        reply = reply + "\nللتواصل مع الموظف: " + bot.handover_number
    db.add(Message(conversation_id=conversation.id, sender="bot", content=reply))
    db.commit()

    token = decrypt_secret(channel_config.access_token) if channel_config.access_token else ""
    if channel == "whatsapp":
        await graph_post(token, f"https://graph.facebook.com/v21.0/{provider_id}/messages", {
            "messaging_product": "whatsapp",
            "to": customer_id,
            "type": "text",
            "text": {"body": reply}
        })
    elif channel == "facebook":
        await graph_post(token, f"https://graph.facebook.com/v21.0/me/messages", {
            "recipient": {"id": customer_id},
            "message": {"text": reply}
        })

@router.get("/meta")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    provider_id = value.get("metadata", {}).get("phone_number_id")
                    for message in value.get("messages", []):
                        if message.get("type") == "text":
                            await process_message(
                                db, "whatsapp", provider_id,
                                message.get("from", ""),
                                message.get("text", {}).get("body", "")
                            )

        elif data.get("object") == "page":
            for entry in data.get("entry", []):
                page_id = str(entry.get("id", ""))
                for event in entry.get("messaging", []):
                    if event.get("message", {}).get("is_echo"):
                        continue
                    sender = event.get("sender", {}).get("id")
                    text = event.get("message", {}).get("text", "")
                    await process_message(db, "facebook", page_id, sender, text)

                for change in entry.get("changes", []):
                    if change.get("field") != "feed":
                        continue
                    value = change.get("value", {})
                    if value.get("item") == "comment" and value.get("verb") == "add":
                        comment_id = value.get("comment_id")
                        message = value.get("message", "")
                        channel_config = get_config_for_provider(db, "facebook", page_id)
                        if not channel_config or not message:
                            continue
                        user = db.query(User).filter(User.id == channel_config.user_id).first()
                        bot = db.query(BotConfig).filter(BotConfig.user_id == user.id).first() if user else None
                        if not user or not bot or not subscription_active(user) or not bot.is_active:
                            continue
                        action = await decide_action(
                            owner_prompt(bot),
                            message,
                            "facebook_comment",
                            parse_products(bot.products)
                        )
                        if action["action"] == "ignore":
                            continue
                        reply = action.get("reply") or await generate_response(owner_prompt(bot), message, bot.tone)
                        if action["action"] == "handover" and bot.handover_number:
                            reply = reply + "\nللتواصل: " + bot.handover_number
                        token = decrypt_secret(channel_config.access_token)
                        sender_id = value.get("from", {}).get("id")
                        if action["action"] == "reply_private" and sender_id:
                            await graph_post(token, "https://graph.facebook.com/v21.0/me/messages", {"recipient": {"id": sender_id}, "message": {"text": reply}})
                        else:
                            await graph_post(token, f"https://graph.facebook.com/v21.0/{comment_id}/comments", {"message": reply})

    except Exception as exc:
        print(f"Webhook processing error: {exc}")
        # Return 200 so Meta does not aggressively retry malformed/non-actionable events.
    return {"status": "ok"}
