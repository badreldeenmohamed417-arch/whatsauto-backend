from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ai import generate_response

router = APIRouter()

# Verify token for Meta Webhooks
VERIFY_TOKEN = "my_secure_verify_token"

@router.get("/webhooks/meta")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/webhooks/meta")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    # Process Meta webhook data (WhatsApp, Messenger, Facebook Comments)
    print("Received webhook:", data)
    
    # Example parsing logic (simplified)
    try:
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for message in value["messages"]:
                            sender_phone = message.get("from")
                            text = message.get("text", {}).get("body", "")
                            
                            # Use AI service
                            ai_reply = await generate_response(
                                system_prompt="You are a helpful customer service AI for WhatsAuto.",
                                user_message=text
                            )
                            print(f"Replying to WhatsApp user {sender_phone} with: {ai_reply}")
                            # TODO: Send API request to WhatsApp Graph API to send `ai_reply`
                            
        elif data.get("object") == "page":
            for entry in data.get("entry", []):
                # Handle Messenger or Comments
                if "messaging" in entry:
                    # Messenger
                    for event in entry["messaging"]:
                        sender_psid = event["sender"]["id"]
                        text = event.get("message", {}).get("text", "")
                        
                        ai_reply = await generate_response(
                            system_prompt="You are a helpful customer service AI for WhatsAuto.",
                            user_message=text
                        )
                        print(f"Replying to Messenger user {sender_psid} with: {ai_reply}")
                        # TODO: Send API request to Messenger Graph API
                        
                elif "changes" in entry:
                    # Facebook Comments
                    for change in entry["changes"]:
                        if change.get("field") == "feed":
                            value = change["value"]
                            if value.get("item") == "comment" and value.get("verb") == "add":
                                comment_id = value["comment_id"]
                                message = value["message"]
                                
                                ai_reply = await generate_response(
                                    system_prompt="You are a helpful customer service AI. Reply to the Facebook comment. Say you will message them privately if appropriate.",
                                    user_message=message
                                )
                                print(f"Replying publicly to comment {comment_id}: {ai_reply}")
                                # TODO: Send public reply via Graph API
                                # TODO: Send private message via Messenger if possible

    except Exception as e:
        print(f"Error processing webhook: {e}")
        
    return {"status": "ok"}
