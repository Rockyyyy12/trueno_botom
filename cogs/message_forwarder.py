import discord
from discord.ext import commands
from config import FORWARDER_CHANNEL_ID

class ChannelSelect(discord.ui.Select):
    def __init__(self, bot, message_content):
        self.bot = bot
        self.message_content = message_content
        options = []
        super().__init__(
            placeholder="Select a channel to forward the message",
            min_values=1, max_values=1, options=options,
            custom_id="channel_select"
        )

    async def callback(self, interaction: discord.Interaction):
        # Try to interpret the value as a channel ID if not in options
        value = self.values[0]
        try:
            channel_id = int(value)
            channel = self.bot.get_channel(channel_id)
        except ValueError:
            channel = None
        if not channel:
            # Try to get from select options if not a valid ID
            channel = self.bot.get_channel(int(self.values[0])) if self.values[0].isdigit() else None
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(self.message_content)
            await interaction.response.send_message(f"Message forwarded to {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to forward message. Please select a valid channel.", ephemeral=True)

class ChannelIdInput(discord.ui.Modal):
    def __init__(self, bot, message_content):
        super().__init__(title="Manual Channel ID Forward")
        self.bot = bot
        self.message_content = message_content
        self.channel_id = discord.ui.TextInput(
            label="Channel ID",
            placeholder="Paste a channel ID to forward the message",
            required=True
        )
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: discord.Interaction):
        channel_id = self.channel_id.value.strip()
        if not channel_id.isdigit():
            await interaction.response.send_message("Invalid channel ID.", ephemeral=True)
            return
        channel = self.bot.get_channel(int(channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(self.message_content)
            await interaction.response.send_message(f"Message forwarded to {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to forward message. Please enter a valid channel ID.", ephemeral=True)

class ManualChannelIdButton(discord.ui.Button):
    def __init__(self, bot, message_content):
        super().__init__(label="Or enter Channel ID manually", style=discord.ButtonStyle.primary)
        self.bot = bot
        self.message_content = message_content

    async def callback(self, interaction: discord.Interaction):
        modal = ChannelIdInput(self.bot, self.message_content)
        await interaction.response.send_modal(modal)

class ChannelSelectView(discord.ui.View):
    def __init__(self, bot, message_content, options):
        super().__init__(timeout=60)
        self.bot = bot
        self.message_content = message_content
        select = ChannelSelect(bot, message_content)
        select.options = options
        self.add_item(select)
        self.add_item(ManualChannelIdButton(bot, message_content))

class MessageForwarder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = FORWARDER_CHANNEL_ID  # Replace with your source channel ID

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != self.target_channel_id:
            return
        content = message.content
        if message.attachments:
            attachment_urls = '\n'.join([a.url for a in message.attachments])
            if content:
                content += f"\n{attachment_urls}"
            else:
                content = attachment_urls
        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in message.guild.text_channels if ch.permissions_for(message.guild.me).send_messages
        ]
        options = options[:25]
        if not options:
            return
        view = ChannelSelectView(self.bot, content, options)
        try:
            await message.reply(
                f"Select a channel to forward the message:",
                view=view
            )
        except Exception as e:
            print(f"Failed to send selector message: {e}")

async def setup(bot):
    await bot.add_cog(MessageForwarder(bot))