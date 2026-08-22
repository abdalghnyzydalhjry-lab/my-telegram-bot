import telebot
import requests

TOKEN = "8843530947:AAEkY0moctJyqY-T6chUSEDGJMrR-9ffiC4"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)

def get_available_models():
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json().get('data', [])
            valid_models = []
            for item in data:
                m_id = item.get('id', '')
                if not any(x in m_id.lower() for x in ['whisper', 'orpheus', 'tts', 'audio', 'vision', 'safetensors']):
                    valid_models.append(m_id)
            return valid_models
    except Exception as e:
        print(f"Error fetching models: {e}")
    return []

AVAILABLE_MODELS = get_available_models()

def ask_groq(prompt_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if not AVAILABLE_MODELS:
        return "❌ لا توجد نماذج نصية متاحة في حسابك حالياً."

    last_error = ""
    for model in AVAILABLE_MODELS:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            data = res.json()
            if res.status_code == 200:
                return data['choices'][0]['message']['content']
            else:
                last_error = f"({model}) -> " + str(data.get('error', {}).get('message', res.text))
        except Exception as e:
            last_error = str(e)
            
    return f"❌ خطأ من السيرفر:\n{last_error}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! 👋 أنا بوت الذكاء الاصطناعي، اسألني أي سؤال وسيتم الرد عليك فوراً.")

@bot.message_handler(func=lambda message: True)
def answer_anything(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_groq(message.text)
    bot.reply_to(message, reply)

bot.infinity_polling(skip_pending=True)
  
