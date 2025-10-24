import discord
from discord.ext import commands
from config import AUTO_FORWARD_CHANNEL_PAIRS

class MessageAutoForward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # List of (source_channel_id, target_channel_id) pairs
        self.channel_pairs = AUTO_FORWARD_CHANNEL_PAIRS

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for source_id, target_id in self.channel_pairs:
            if message.channel.id == source_id:
                target_channel = self.bot.get_channel(target_id)
                if not target_channel:
                    continue
                content = message.content
                if message.attachments:
                    attachment_urls = '\n'.join([a.url for a in message.attachments])
                    if content:
                        content += f"\n{attachment_urls}"
                    else:
                        content = attachment_urls
                await target_channel.send(content)

async def setup(bot):
    await bot.add_cog(MessageAutoForward(bot))