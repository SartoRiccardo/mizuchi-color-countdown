#!/usr/bin/env python3
import json
import discord
from discord.ext import commands


def get_config():
    fin = open("config.json")
    data = json.loads(fin.read())
    fin.close()
    return data["config"]


config = get_config()
DEFAULT_PREFIX = "-" if not ("prefix" in config) else config["prefix"]
bot = commands.Bot(command_prefix=DEFAULT_PREFIX)


if __name__ == '__main__':
    bot.remove_command("help")
    bot.load_extension("cogs.owner")

    cogs = ["countdown"]
    for cog in cogs:
        try:
            bot.load_extension(f"cogs.{cog}")
        except discord.ext.commands.errors.ExtensionNotFound as e:
            print(f"Could not load {e.name}")

    bot.run(config["token"])
