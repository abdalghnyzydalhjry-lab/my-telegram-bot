import telebot
import requests
from datetime import date

TOKEN = "8843530947:AAEkY0moctJyqY-T6chUSEDGJMrR-9ffiC4"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)

# قاموس لتتبع عدد أسئلة المستخدمين
user_usage = {}

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
    bot.reply_to(message, "أهلاً بك! 👋 أنا بوت الذكاء الاصطناعي. لديك 5 أسئلة مجانية يومياً، تفضل بطرح سؤالك.")

@bot.message_handler(func=lambda message: True)
def answer_anything(message):
    user_id = message.from_user.id
    today = str(date.today())

    # تهيئة بيانات المستخدم للترسيت اليومي
    if user_id not in user_usage or user_usage[user_id]['date'] != today:
        user_usage[user_id] = {'count': 0, 'date': today}

    # التحقق من تجاوز الحد المسموح
    if user_usage[user_id]['count'] >= 5:
        msg = (
            "⚠️ **عذراً، لقد استهلكت حدك اليومي المجاني (5 أسئلة)!**\n\n"
            "للاشتراك المفتوح بدون حدود، يرجى التواصل مع المطور للتفعيل."
        )
        bot.reply_to(message, msg, parse_mode="Markdown")
        return

    # زيادة العداد وإرسال الإجابة
    user_usage[user_id]['count'] += 1
    remains = 5 - user_usage[user_id]['count']
    
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_groq(message.text)
    
    full_reply = f"{reply}\n\n*📊 متبقي لك اليوم: {remains} أسئلة.*"
    bot.reply_to(message, full_reply, parse_mode="Markdown")

bot.infinity_polling(skip_pending=True)
