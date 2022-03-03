import discord
from discord.ext import tasks, commands
import importlib
import json
import re
from datetime import datetime
import aiofiles
from discord.ext import commands


SUCCESS_REACTION = '\N{THUMBS UP SIGN}'


class Countdown(commands.Cog):
    REVEAL_DATE = "28 February 2022"

    def __init__(self, bot):
        self.bot = bot
        self.update_message.start()
        self.update_emote.start()

    def cog_unload(self):
        self.update_message.stop()
        self.update_emote.stop()

    @staticmethod
    def get_days_passed():
        difference = datetime.now() - datetime.strptime(Countdown.REVEAL_DATE, "%d %B %Y")
        return int(difference.total_seconds() / (60*60*24)) + 1

    # EMOTE #

    @tasks.loop(seconds=60*60)
    async def update_emote(self):
        fin = await aiofiles.open("config.json")
        data = json.loads(await fin.read())["emote"]
        await fin.close()

        if data["id"] is None:
            print("emote id is null")
            return

        emote = self.get_emote(data["id"])
        if emote is None:
            print("Cannot find the emote!")
            return

        new_emote_name = data["template"].format(self.get_days_passed())
        if emote.name == new_emote_name:
            return
        await emote.edit(name=new_emote_name)

    @commands.command()
    @commands.has_role("Jailbreak Kings")
    async def setemote(self, ctx, emote):
        reg = r":.+?:(\d+)"
        emote_id = int(re.findall(reg, emote)[0])

        fin = await aiofiles.open("config.json")
        data = json.loads(await fin.read())
        data["emote"]["id"] = emote_id
        await fin.close()

        fout = await aiofiles.open("config.json", "w")
        await fout.write(json.dumps(data))
        await fout.close()

        await ctx.message.add_reaction(SUCCESS_REACTION)

    def get_emote(self, emote_id):
        for guild in self.bot.guilds:
            emote = discord.utils.get(guild.emojis, id=emote_id)
            if emote:
                return emote
        return None

    # MESSAGE #

    @tasks.loop(seconds=60*60)
    async def update_message(self):
        fin = await aiofiles.open("config.json")
        config = json.loads(await fin.read())
        data = config["message"]
        await fin.close()

        if data["channel_id"] is None:
            print("channel_id is not set!")
            return

        days = self.get_days_passed()
        template = data["template"]
        message_text = template.format(days)

        if data["message_id"] is None:
            await self.send_message(data["channel_id"], message_text)
        else:
            message = await self.get_channel_message(data["channel_id"], data["message_id"])
            if not message:
                await self.send_message(data["channel_id"], message_text)
            else:
                await message.edit(content=message_text)

    async def send_message(self, channel_id, text=None):
        fin = await aiofiles.open("config.json")
        config = json.loads(await fin.read())
        await fin.close()

        if text is None:
            template = config["message"]["template"]
            text = template.format(self.get_days_passed())

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, id=channel_id)
            if channel:
                config["message"]["message_id"] = (await channel.send(text)).id
                config["message"]["channel_id"] = channel_id
                fout = await aiofiles.open("config.json", "w")
                await fout.write(json.dumps(config))
                await fout.close()

    @commands.command()
    @commands.has_role("Jailbreak Kings")
    async def setchannel(self, ctx, channel_mention):
        channel_id = int(channel_mention[2:-1])
        await self.send_message(channel_id)
        await ctx.message.add_reaction(SUCCESS_REACTION)

    async def get_channel_message(self, channel_id, message_id):
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, id=channel_id)
            if channel:
                try:
                    return await channel.fetch_message(message_id)
                except discord.NotFound:
                    print(f"Message with ID {message_id} in channel {channel_id} was not found!")
                    return None
        return None


def setup(bot):
    bot.add_cog(Countdown(bot))
