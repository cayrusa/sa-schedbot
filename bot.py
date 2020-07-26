#!/usr/bin/env python3
# coding: utf-8
# SchedBot by Thrombozyt and Fardale
import discord
from discord.ext import commands
import asyncio
import aiohttp
from time import strftime
from datetime import datetime, tzinfo, timezone, timedelta
import conf
import secrets

global connected
connected = False
global lockout
lockout = False


async def ping():
    log_chan = bot.get_channel(conf.LOG_CHAN)
    await log_chan.send("Regular scheduling updates activated")
    it = 0
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://script.google.com/macros/s/AKfycbw8rBUEf_E-zkVzXCC8YM2_awJshEiVRPE3nu53FLIFleNrzOAB/exec"
            ) as r:
                data = await r.read()
        output = parse(data)
        if output != ["Nothing to push!"]:
            sched_chan = bot.get_channel(conf.SCHEDULING_CHAN)
            for line in output:
                await ched_chan.send(line)
        await asyncio.sleep(3600)
        it += 1
        print("Cycle # " + str(it))


def parse(input):
    refine = str(input)
    refine = refine.lstrip("b'").rstrip("'")
    refine = refine.lstrip('"').rstrip('"')
    refine = refine.split("|")
    output = []
    total = 0
    message = ""
    for line in refine:
        total += len(line)
        if total < 1500:
            if not message == "":
                message += "\n"
            message += line
        else:
            output.append(message)
            total = 0
            message = line
    output.append(message)
    return output


def is_admin(user):
    serv = bot.get_guild(conf.SERVER)
    user = serv.get_member(user.id)
    if user is None:
        return False
    else:
        return conf.ADMIN_ROLE in user.roles


bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    global connected
    if not connected:
        connected = True
        print(f"Hi. I'm {bot.user.name}")
        print("Ready and waiting")
        log_chan = bot.get_channel(conf.LOG_CHAN)
        await log_chan.send("SchedBot here. Ready and waiting.")
        await ping()


@bot.event
async def on_member_join(member):
    message = member.name + " has **joined** the server"
    print(message)
    channel = bot.get_channel(conf.JOINS_LEAVES_CHAN)
    await channel.send(message)
    await member.send(conf.WELCOME_MSG)


@bot.event
async def on_member_remove(member):
    message = member.name + " has **left** the server"
    print(message)
    channel = bot.get_channel(conf.JOINS_LEAVES_CHAN)
    await channel.send(message)


@bot.command()
async def lfg(ctx):
    userID = ctx.message.author.id
    serv = bot.get_guild(conf.SERVER)
    member = serv.get_member(userID)
    if member is None:
        await ctx.send("You are not a member of the TI:SA discord server")
        return
    role = serv.get_role(conf.LFG_ROLE)
    await member.add_roles(role)
    print(f"add lfg for {ctx.message.author.name}")


@bot.command()
async def rmlfg(ctx):
    userID = ctx.message.author.id
    serv = bot.get_guild(conf.SERVER)
    try:
        member = discord.utils.get(serv.members, id=userID)
    except:
        await ctx.send("You are not a member of the TI:SA discord server")
        return
    role = serv.get_role(conf.LFG_ROLE)
    await member.remove_roles(role)
    print("remove lfg for " + ctx.message.author.name)


@bot.command()
async def shutdown(ctx):
    if is_admin(ctx.message.author):
        print(f"Shutdown denied for {ctx.message.author.name}:{ctx.message.author.id}")
        await ctx.send("Access denied")
    else:
        print(f"Shutdown by {ctx.message.author.name}")
        await bot.logout()


@bot.command()
async def push(ctx):
    if is_admin(ctx.message.author):
        await ctx.send("Access denied")
    else:
        channel = bot.get_channel(conf.SCHEDULING_CHAN)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://script.google.com/macros/s/AKfycbw8rBUEf_E-zkVzXCC8YM2_awJshEiVRPE3nu53FLIFleNrzOAB/exec"
            ) as r:
                data = await r.read()
        output = parse(data)
        for line in output:
            await channel.send(line)
    print("Push")


@bot.command()
async def schedule(ctx):
    user = ctx.message.author
    userID = ctx.message.author.id
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://script.google.com/macros/s/AKfycbw67eHlfhmAkx2URix9QBhV2qMiIJEfWRt55OTRMgYkY39oJNt4/exec?{}".format(
                userID
            )
        ) as r:
            data = await r.read()
    test = str(data)
    refine = test.lstrip("b'").rstrip("'")
    await user.send(refine)
    print("Schedule for " + ctx.message.author.name)


@bot.command()
async def commands(ctx):
    print(f"Commands for {ctx.message.author.name}")
    user = ctx.message.author
    await user.send(
        "__**Schedbot commands:**__ \n \n***!info Playername***\nGet a summary of all your games, and whether they have been scheduled.\n> Playername is your name as written in the Player List sheet of the Game Manager.\n>If no Playername is given, the bot will send you your own info."
    )
    await user.send(
        '***!update Game# yes/maybe/no comment***\nQuickly confirm or cancel your participation in a scheduled game.\n> Game# is the number of the game as announced by the bot.\n> yes/no/maybe indicates your answer. Yes confirms your participation, no cancels the date, maybe indicates that there might be problems on your end.\n> comment is a comment that you can leave for your opponents.\nExample: ***!update 27 yes "It\'s gonna be awesome"***'
    )
    await user.send(
        "***!schedule***\nSends you a link to the scheduling form prefilled with your player name and all the times you have already submitted."
    )
    await user.send(
        "***!lfg***\nGives you the Looking-for-Game role in Discord. This will put you at the top of the user list and set your nick to yellow.\n>To remove your status use the command *!rmlfg*."
    )
    await user.send(
        "***!time Game#***\n Dual use command to help coordinating timezones.\n>If you just type *!time* the bot will return the current time in the Central European Timezone which this community uses as reference.\n>You can specify a game number and - if the game is scheduled - the bot will give you the time remaining until the scheduled date & time."
    )
    await user.send(
        "***!status Game# Messages***\nGives you the current status of a game with an overview of the player responses (for scheduled games). You can also look into the game log.\n>Game# is the number of the game as announced by the bot.\n>Messages can be specified with ***full*** or ***recent***.\n>*recent* will give you the 10 last entries in the log.\n>*full* will give you the entire history of the game.\n>The default value for messages is to just return status and nothing from the log."
    )


@bot.command()
async def update(ctx, game, choice="none", comment="none"):
    print("Update by " + ctx.message.author.name)
    global lockout
    availchoice = ["yes", "no", "maybe", "none"]
    if choice not in availchoice:
        await ctx.send("Invalid command.")
    else:
        while lockout:
            await asyncio.sleep(5)
        lockout = True
        comment = comment.replace(" ", "_")
        user = ctx.message.author.id
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://script.google.com/macros/s/AKfycbzdDzETHtNVkD-3u8M1ff0nxeHoAQeiudCdjZYE68Cd70K6DD1W/exec?{}&{}&{}&{}".format(
                    user, game, choice, comment
                )
            ) as r:
                data = await r.read()
        output = parse(data)
        for line in output:
            await ctx.send(line)
        await asyncio.sleep(30)
        if choice != "no":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://script.google.com/macros/s/AKfycbwZXSh--oibWkTweEOZdgEMr2vGUUcrgM_iBslu_vipTlJ2OQ0/exec?{}".format(
                        game
                    )
                ) as r:
                    data = await r.read()
            output = parse(data)
            for line in output:
                await ctx.send(line)
        lfg = bot.get_channel(conf.SCHEDULING_CHAN)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://script.google.com/macros/s/AKfycbw8rBUEf_E-zkVzXCC8YM2_awJshEiVRPE3nu53FLIFleNrzOAB/exec"
            ) as r:
                data = await r.read()
        output = parse(data)
        if output != ["Nothing to push!"]:
            for line in output:
                await lfg.send(line)
        await asyncio.sleep(10)
        lockout = False


@bot.command()
async def status(ctx, game, content="no"):
    print("Status for " + ctx.message.author.name)
    user = ctx.message.author
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://script.google.com/macros/s/AKfycbwZXSh--oibWkTweEOZdgEMr2vGUUcrgM_iBslu_vipTlJ2OQ0/exec?{}&{}".format(
                game, content
            )
        ) as r:
            data = await r.read()
    output = parse(data)
    for line in output:
        await user.send(line)


@bot.command()
async def time(ctx, game=None):
    print("Time for " + ctx.message.author.name)
    if game == None:
        test = ctx.message.timestamp
        offset = timedelta(hours=1)
        zone = timezone(offset, "CET")
        local = test.replace(tzinfo=timezone.utc).astimezone(tz=zone)
        curtime = local.strftime("%a, %d %b %Y %H:%M:%S CET (UTC+1)")
        await ctx.send("The current time is: " + curtime)
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://script.google.com/macros/s/AKfycbwcIWUcIk_TnnXe49vZsKgUUrjRRHp8PXfptJ-3WbfsRjJZuqM/exec?{}".format(
                    game
                )
            ) as r:
                data = await r.read()
        message = parse(data)
        for line in message:
            await ctx.send(line)


@bot.command()
async def info(ctx, player="ID"):
    user = ctx.message.author
    if player == "ID":
        print("Info for " + ctx.message.author.name)
        player = "ID&{}".format(ctx.message.author.id)
    elif player == "time":
        print("Info for " + ctx.message.author.name)
        player = "time&ID&{}".format(ctx.message.author.id)
    else:
        print("Checking data for player " + player)
    player = player.replace(" ", "_")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://script.google.com/macros/s/AKfycbw7-yoLcBSnmCcWYWpd3_hITb0NsH8hAh9o6dURkpQeFihlKJyF/exec?{}".format(
                player
            )
        ) as r:
            data = await r.read()
    output = parse(data)
    for line in output:
        await user.send(line)


@bot.command()
async def match(ctx, player1="gm", player2=""):
    print("Querry continuations by {}".format(ctx.message.author.name))
    if player1 == "lfg":
        lfg = ["PlayerID"]
        for member in ctx.message.guild.members:
            re_member = member
            for role in member.roles:
                if role.name == "Looking for a Game":
                    if re_member.status != Status.offline:
                        lfg.append(re_member.id)
        del lfg[0]
        if len(lfg) > 0:
            player1 += ","
            for ID in lfg:
                player1 = player1 + "&{}".format(ID)
        else:
            player1 = ""
    if player2 == "":
        player = player1
    else:
        player = player1 + "," + player2
    player = player.replace(", ", ",")  # TODO can do better
    player = player.replace(" ", "_")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://script.google.com/macros/s/AKfycbxZnLxVemWiguQVUDh5iCzqjNFyD3dDcsiKDXmQiQ/exec?"
            + player
        ) as r:
            data = await r.read()
    output = parse(data)
    for line in output:
        await ctx.send(line)


@bot.command()
async def statistics(ctx, player="ID"):
    user = ctx.message.author
    if player == "ID":
        print("Racial Stats for " + ctx.message.author.name)
        player = "ID&{}".format(ctx.message.author.id)
    else:
        print("Checking Racial stats for player " + player)
    player = player.replace(" ", "_")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://script.google.com/macros/s/AKfycbwls2PNCXIteMleBA8q8IKgGyTAYcPVJYsQX7recQ/exec?"
            + player
        ) as r:
            data = await r.read()
    output = parse(data)
    for line in output:
        await user.send(line)


if __name__ == "__main__":
    bot.run(secrets.TOKEN, reconnect=False)
