import os
from groq import AsyncGroq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

async def generate_response(system_prompt: str, user_message: str, tone: str = "professional") -> str:
    """Generate a response using Groq."""
    
    if not groq_client:
        return "لم يتم إعداد مفتاح GROQ API. الرجاء إضافته في إعدادات البيئة."

    messages = [
        {"role": "system", "content": f"{system_prompt}\nKeep responses under 300 tokens, avoid unnecessary explanations, and use a {tone} tone."},
        {"role": "user", "content": user_message}
    ]
    
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192", # Fast and cheap model suitable for customer support
            max_tokens=300,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API failed: {e}")
        return "عذراً، لا يمكنني الرد حالياً بسبب مشكلة في الاتصال بالذكاء الاصطناعي."
