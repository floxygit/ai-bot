import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
import json

load_dotenv('config.env')

CHANNEL_ID = os.getenv('CHANNEL_ID')
if CHANNEL_ID:
    CHANNEL_ID = [int(x) for x in CHANNEL_ID.split(',')]
else:
    CHANNEL_ID = []

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

AI_API_KEY = os.getenv('AI_API_KEY')
AI_API_MODEL = os.getenv('AI_API_MODEL')
AI_API_URL = os.getenv('AI_API_URL')
AI_SYSTEM_PROMPT = os.getenv('AI_SYSTEM_PROMPT')
BOT_TOKEN = os.getenv('BOT_TOKEN')

CHAT_HISTORY_FILE = 'data/chatHistory.json'
CHAT_HISTORY_LIMIT = 5

def load_history():
    try:
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_history(data):
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if CHANNEL_ID and message.channel.id not in CHANNEL_ID:
        return
    if not (message.content.startswith(f'<@!{bot.user.id}>') or message.content.startswith(f'<@{bot.user.id}>')):
        return

    content = message.content.split(maxsplit=1)
    if len(content) < 2:
        return
    user_msg = content[1]

    history = load_history()
    user_id = str(message.author.id)
    if user_id not in history:
        history[user_id] = []
    history[user_id].append({"role": "user", "content": user_msg})
    history[user_id] = history[user_id][-CHAT_HISTORY_LIMIT:]

    messages = []
    if AI_SYSTEM_PROMPT:
        messages.append({"role": "system", "content": AI_SYSTEM_PROMPT})
    messages.extend(history[user_id])

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_API_MODEL,
        "messages": messages
    }

    async with message.channel.typing():
        async with aiohttp.ClientSession() as session:
            async with session.post(AI_API_URL, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    try:
                        reply = data['choices'][0]['message']['content']
                    except (KeyError, IndexError):
                        reply = "Sorry, I couldn't generate a response."
                else:
                    reply = "Error with the API request."

    history[user_id].append({"role": "assistant", "content": reply})
    history[user_id] = history[user_id][-CHAT_HISTORY_LIMIT:]
    save_history(history)

    await message.reply(reply)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in config.env")

bot.run(BOT_TOKEN)
