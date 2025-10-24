import discord
from discord.ext import commands
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODMAIL_CATEGORY_ID, STAFF_ROLE_ID

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_id = MODMAIL_CATEGORY_ID
        self.staff_role_id = STAFF_ROLE_ID
        self.user_channel_map = {}  # user_id: channel_id

    async def get_or_create_modmail_channel(self, user, guild):
        category = discord.utils.get(guild.categories, id=self.category_id)
        if not category:
            return None
        channel_name = f"{user.name.lower().replace(' ', '-')}"
        # Check if a channel already exists for this user
        for channel in category.text_channels:
            if channel.topic and str(user.id) in channel.topic:
                return channel
        # Create a new channel for the user
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_role(self.staff_role_id): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Modmail thread for {user} ({user.id})"
        )
        self.user_channel_map[user.id] = channel.id
        return channel

    async def close_modmail(self, user, guild):
        category = discord.utils.get(guild.categories, id=self.category_id)
        if not category:
            return False
        for channel in category.text_channels:
            if channel.topic and str(user.id) in channel.topic:
                await channel.delete(reason="Modmail closed")
                self.user_channel_map.pop(user.id, None)
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # Handle DMs to the bot
        if isinstance(message.channel, discord.DMChannel):
            for guild in self.bot.guilds:
                category = discord.utils.get(guild.categories, id=self.category_id)
                if not category:
                    continue
                open_channel = None
                for channel in category.text_channels:
                    if channel.topic and str(message.author.id) in channel.topic:
                        open_channel = channel
                        break
                if open_channel:
                    # If user sends 'close', close the chat
                    if message.content.strip().lower() == 'close chat':
                        closed = await self.close_modmail(message.author, guild)
                        if closed:
                            await message.channel.send("Your modmail chat has been closed.")
                        else:
                            await message.channel.send("No open modmail chat found to close.")
                    else:
                        # Forward the message to the open modmail channel
                        await open_channel.send(f"**User:** {message.author} ({message.author.id})\n{message.content}")
                    return
                # If not open, create a new channel
                channel = await self.get_or_create_modmail_channel(message.author, guild)
                if channel:
                    await channel.send(f"**User:** {message.author} ({message.author.id})\n{message.content}")
                    await channel.send(view=StaffCloseView(self, message.author, guild))
                await message.channel.send("Your message has been sent to the staff. They will reply here. Type 'close' to end this chat.")
        # Handle staff replies in modmail channels
        elif message.guild and message.channel.category and message.channel.category.id == self.category_id:
            # Only allow staff to reply
            if self.staff_role_id in [role.id for role in message.author.roles]:
                try:
                    user_id = int(message.channel.topic.split('(')[-1].replace(')', ''))
                    user = self.bot.get_user(user_id)
                    if user:
                        if message.content.strip().lower() == 'close chat':
                            closed = await self.close_modmail(user, message.guild)
                            if closed:
                                await message.channel.send("Modmail chat closed.")
                                await user.send("Your modmail chat has been closed by staff.")
                        else:
                            await user.send(f"**Staff:**\n{message.content}")
                except Exception:
                    pass

class UserCloseView(discord.ui.View):
    def __init__(self, modmail_cog, user, guild):
        super().__init__(timeout=None)
        # No button added for user anymore
        # self.modmail_cog = modmail_cog
        # self.user = user
        # self.guild = guild
        # self.add_item(UserCloseButton(modmail_cog, user, guild))

class StaffCloseView(discord.ui.View):
    def __init__(self, modmail_cog, user, guild):
        super().__init__(timeout=None)
        self.modmail_cog = modmail_cog
        self.user = user
        self.guild = guild
        self.add_item(StaffCloseButton(modmail_cog, user, guild))

class StaffCloseButton(discord.ui.Button):
    def __init__(self, modmail_cog, user, guild):
        super().__init__(label="Close Chat (Staff)", style=discord.ButtonStyle.danger)
        self.modmail_cog = modmail_cog
        self.user = user
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        # Show confirmation view
        await interaction.response.send_message(
            "Are you sure you want to close this modmail chat?",
            view=StaffCloseConfirmView(self.modmail_cog, self.user, self.guild),
            ephemeral=True
        )

class StaffCloseConfirmView(discord.ui.View):
    def __init__(self, modmail_cog, user, guild):
        super().__init__(timeout=60)
        self.modmail_cog = modmail_cog
        self.user = user
        self.guild = guild
        self.add_item(StaffConfirmButton(modmail_cog, user, guild))
        self.add_item(StaffCancelButton())

class StaffConfirmButton(discord.ui.Button):
    def __init__(self, modmail_cog, user, guild):
        super().__init__(label="Confirm Close", style=discord.ButtonStyle.danger)
        self.modmail_cog = modmail_cog
        self.user = user
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        closed = await self.modmail_cog.close_modmail(self.user, self.guild)
        if closed:
            await interaction.response.edit_message(content="Modmail chat closed.", view=None)
            try:
                await self.user.send("Your modmail chat has been closed by staff.")
            except Exception:
                pass
        else:
            await interaction.response.edit_message(content="No open modmail chat found to close.", view=None)

class StaffCancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back to Chat", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Close cancelled. You are back in the chat.", view=None)

async def setup(bot):
    await bot.add_cog(ModMail(bot))
