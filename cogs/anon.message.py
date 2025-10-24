import discord
from discord import app_commands
from discord.ext import commands
import random

class AnonModal(discord.ui.Modal, title="Send Anonymous Message"):
    user_name = discord.ui.TextInput(label="Name of user", placeholder="Enter a display name (optional)", required=False)
    header_url = discord.ui.TextInput(label="Header/Profile Image URL", placeholder="Paste an image URL (optional)", required=False)
    message_title = discord.ui.TextInput(label="Message Title", placeholder="Enter a title for your message (optional)", required=False)
    message_content = discord.ui.TextInput(label="Message Content", style=discord.TextStyle.paragraph, required=True, max_length=2000)
    channel_id = discord.ui.TextInput(label="Channel ID to Post In", placeholder="Paste the channel ID", required=True)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.random_names = [
            "Anonymous Cat", "Mysterious Fox", "Hidden Owl", "Secret Squirrel", "Masked Panda",
            "Nameless Wolf", "Unknown Tiger", "Silent Eagle", "Ghost Bear", "Shadow Rabbit"
        ]

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel = self.bot.get_channel(int(self.channel_id.value))
            if not channel or not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message("Invalid channel ID.", ephemeral=True)
                return
            name = self.user_name.value.strip() if self.user_name.value.strip() else random.choice(self.random_names)
            avatar_url = self.header_url.value.strip() if self.header_url.value.strip() else None
            title = self.message_title.value.strip()
            if title:
                content = f"## **{title}**\n{self.message_content.value}"
            else:
                content = self.message_content.value
            webhook = await channel.create_webhook(name=name, avatar=None)
            await webhook.send(
                content=content,
                username=name,
                avatar_url=avatar_url
            )
            await webhook.delete()
            await interaction.response.send_message("Your anonymous message has been sent!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

class AnonMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anon", description="Send an anonymous message to a channel.")
    async def anon(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AnonModal(self.bot))

async def setup(bot):
    await bot.add_cog(AnonMessage(bot))
