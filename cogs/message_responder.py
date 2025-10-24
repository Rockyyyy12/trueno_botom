import discord
from discord.ext import commands
import json
import os

class MessageResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load triggers and responses from JSON file
        json_path = os.path.join(os.path.dirname(__file__), "message_triggers.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.trigger_responses = {k: v["triggers"] for k, v in data.items()}
        self.responses = {k: v["response"] for k, v in data.items()}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        content = message.content.lower()
        for key, words in self.trigger_responses.items():
            if any(word in content for word in words):
                await message.channel.send(self.responses[key])
                break
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(MessageResponder(bot))