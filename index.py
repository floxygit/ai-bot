import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp

load_dotenv('config.env')

CHANNEL_ID = []  # e.g. [123456789012345678, 987654321098765432]; empty = no reaction

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

AI_API_KEY = os.getenv('AI_API_KEY')
AI_API_MODEL = os.getenv('AI_API_MODEL')
AI_API_URL = os.getenv('AI_API_URL')
AI_SYSTEM_PROMPT = os.getenv('AI_SYSTEM_PROMPT')
BOT_TOKEN = os.getenv('BOT_TOKEN')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if CHANNEL_ID and message.channel.id not in CHANNEL_ID:
        return
    if message.content.startswith(f'<@!{bot.user.id}>') or message.content.startswith(f'<@{bot.user.id}>'):
        content = message.content.split(maxsplit=1)
        if len(content) < 2:
            return
        user_msg = content[1]

        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = []
        if AI_SYSTEM_PROMPT:
            messages.append({"role": "system", "content": AI_SYSTEM_PROMPT})
        messages.append({"role": "user", "content": user_msg})

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

        await message.reply(reply)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in config.env")

bot.run(BOT_TOKEN)
