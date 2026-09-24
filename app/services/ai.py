import os
from groq import AsyncGroq
import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

async def generate_response(system_prompt: str, user_message: str, tone: str = "professional") -> str:
    """Generate a response using Groq, with fallback to DeepSeek."""
    
    messages = [
        {"role": "system", "content": f"{system_prompt}\nKeep responses under 300 tokens, avoid unnecessary explanations, and use a {tone} tone."},
        {"role": "user", "content": user_message}
    ]
    
    # Try Groq first
    if groq_client:
        try:
            chat_completion = await groq_client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192", # Fast and cheap model
                max_tokens=300,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API failed: {e}")
            pass # Fallback to DeepSeek
    
    # Fallback to DeepSeek
    if DEEPSEEK_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "max_tokens": 300
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"DeepSeek API failed: {e}")
            pass
            
    return "عذراً، لا يمكنني الرد حالياً. يرجى المحاولة لاحقاً."
