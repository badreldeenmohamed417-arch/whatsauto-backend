import os
from groq import AsyncGroq
import google.generativeai as genai

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def generate_response(system_prompt: str, user_message: str, tone: str = "professional") -> str:
    """Generate a response using Groq, with fallback to Gemini."""
    
    # Try Groq first
    if groq_client:
        messages = [
            {"role": "system", "content": f"{system_prompt}\nKeep responses under 300 tokens, avoid unnecessary explanations, and use a {tone} tone."},
            {"role": "user", "content": user_message}
        ]
        try:
            chat_completion = await groq_client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192", 
                max_tokens=300,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API failed: {e}")
            # Fallback to Gemini
            
    # Try Gemini as fallback (or primary if Groq is missing)
    if GEMINI_API_KEY:
        full_prompt = f"{system_prompt}\nKeep responses under 300 tokens, avoid unnecessary explanations, and use a {tone} tone.\n\nUser: {user_message}"
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API failed: {e}")
            
    return "عذراً، لا يمكنني الرد حالياً بسبب مشكلة في الاتصال بالذكاء الاصطناعي."
