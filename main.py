import datetime
import random

import discord
from steam import steamid
from steam.steamid import SteamID
import os
import json
import database
import aiohttp
import time
from discord.ext import commands


class State:
    heroes = None
    items = None
    start_time = None
    idea_time = None

state = State()
file = open('local.json')
config = json.load(file)
state.start_time = time.time()
state.idea_time = time.time()
ONE_DAY = 86400

bot = commands.Bot(command_prefix='!')


@bot.command(name='info')
async def det_info(ctx):
    embed = discord.Embed(
        title='Информация о командах'
    )
    embed.add_field(name='!new <link>', value='Привязка Steam аккаунта к вашему аккаунту Discord', inline=False)
    embed.add_field(name='!account', value='Получить информацию об аккаунте', inline=False)
    embed.add_field(name='!lms <value>', value='Показывает результаты последних матчей, максимальное количество полученных матчей 20. Если количество не задается, то выдается последний матч', inline=False)
    embed.add_field(name='!roll', value='Это чтобы всякие мидеры в пати сразу решили кто в мид идет', inline=False)
    await ctx.reply(embed=embed)


@bot.command(name='new')
async def register(ctx, link=None):
    if link is None:
        message = f"Привет, чтобы я тебя запомнил, мне необходимо отправить ссылку на твоей профиль в Steam \n > !new **steam link**"
        await ctx.author.send(message)
    else:
        steam_id64 = steamid.from_url(link)
        if steam_id64 is None:
            await ctx.channel.send('Ошибка, возможно вы ввели неверную ссылку')
        else:
            steam_id32 = SteamID(steam_id64).as_32
            check = await database.get_steam_id(ctx.author.id)
            if check is None:
                print(steam_id32)
                await database.register(ctx.author, steam_id32, link, steam_id64, discord_id=ctx.author.id)
                await ctx.channel.send("Отлично")
            else:
                await ctx.channel.send(f"К данному Discord аккаунту уже привязан Steam аккаунт")


@bot.command(name='account')
async def account_info(ctx):
    print(ctx.author.id)
    steam_id = await database.get_steam_id(ctx.author.id)
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.opendota.com/api/players/{steam_id[0]}') as response,\
                   session.get(f'https://api.opendota.com/api/players/{steam_id[0]}/wl') as wl:
            json_wl = await wl.json()
            json_response = await response.json()
            try:
                embed = discord.Embed(
                    title=json_response['profile']['personaname'],
                    url=json_response['profile']['profileurl'],
                )
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=ctx.author.avatar_url
                )
                embed.add_field(name='Win', value=json_wl['win'])
                embed.add_field(name='Lose', value=json_wl['lose'])
                embed.set_thumbnail(url=json_response['profile']['avatarfull'])
                await ctx.channel.send(embed=embed)
            except:
                await ctx.channel.send('Не удалось получить информацию об аккаунте.\n'
                                       'Возможно у вас отключена общедоступная история матчей или статистика еще не сформировалась.\n')


@bot.command(name='lms')
async def last_matches(ctx, count: int = 1):
    if count > 20:
        await ctx.channel.send('Сорян, можно получить только полседние 20 матчей')
    else:
        steam_id = await database.get_steam_id(ctx.author.id)
        await get_heroes()
        await get_items()
        if steam_id is not None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f'https://api.opendota.com/api/players/{steam_id[0]}/recentMatches') as matches:

                    json_matches = await matches.json()
                    json_heroes = state.heroes
                    for i in range(count):
                        async with session.get(f'https://api.opendota.com/api/matches/{json_matches[i]["match_id"]}') as match:
                            json_match = await match.json()
                            for player in json_match['players']:
                                if player['account_id'] == steam_id[0]:
                                    my_player = player['personaname']
                                    if player['win'] == 1:
                                        result = 'Won match'
                                    else:
                                        result = 'Lose match'
                                    if player['isRadiant'] is True:
                                        team = 'Radiant'
                                    else:
                                        team = 'Dire'
                                else:
                                    pass
                            for hero in json_heroes:
                                if hero['id'] == json_matches[i]['hero_id']:
                                    embed = discord.Embed(
                                        title=f'{hero["localized_name"]} ({json_match["radiant_score"]}:{json_match["dire_score"]})'
                                    )
                                    embed.set_author(name=f'{ctx.author.display_name} ({my_player})')
                                    embed.set_thumbnail(url=f'https://cdn.cloudflare.steamstatic.com/{hero["img"]}')
                                    embed.add_field(name='Kills', value=json_matches[i]['kills'])
                                    embed.add_field(name='Deaths', value=json_matches[i]['deaths'])
                                    embed.add_field(name='Assists', value=json_matches[i]['assists'])
                                    embed.add_field(name='Duration', value=datetime.timedelta(seconds=int(json_matches[i]['duration'])).__str__())
                                    embed.add_field(name=config['GAME_MODS'][str(json_matches[i]['game_mode'])], value=config['LOBBY_TYPES'][str(json_matches[i]['lobby_type'])])
                                    embed.add_field(name=team, value=result)
                                    embed.add_field(name='Чтобы узнать подробнее о матче, используйте команду',
                                                    value=f'`!m {json_matches[i]["match_id"]}`', inline=False)
                                    await ctx.channel.send(embed=embed)


@bot.command(name='idea')
async def send_idea(ctx):
    current_time = time.time()
    if current_time - state.idea_time < 60:
        ctx.channel.send('Отправлять свою гениальную идею можно раз в минуту')
    else:
        ctx.channel.send(ctx.message)
    state.idea_time = time.time()

# @bot.commands(name='lm')
# async def last_match(ctx, number: int = 1):
#     steam_id = await database.get_steam_id(ctx.author)
#     await get_heroes()
#     await get_items()
#     async with aiohttp.ClientSession() as session:
#         async with session.get(f'https://api.opendota.com/api/players/{steam_id[0]}/matches') as matches:
#             json_matches = await matches.json()
#             match_id = json_matches[number]['match_id']
#             async with session.get(f'https://api.opendota.com/api/matches/{match_id}') as match:
#                 json_match = await match.json()
#                 for player in json_match['players']:
#                     if player['account_id'] == steam_id[0]:
#                         if player['win'] == 1:
#                             result = 'Won match'
#                         else:
#                             result = 'Lose match'
#                     else:
#                         pass
#                 for hero in state.heroes:
#                     if hero['id'] == json_matches[i]['hero_id']:
#                         embed = discord.Embed(
#                             title=hero['localized_name']
#                         )
#                         embed.set_thumbnail(url=f'https://cdn.cloudflare.steamstatic.com/{hero["img"]}')
#                         embed.add_field(name='Kills', value=json_matches[i]['kills'])
#                         embed.add_field(name='Deaths', value=json_matches[i]['deaths'])
#                         embed.add_field(name='Assists', value=json_matches[i]['assists'])
#                         embed.add_field(name='Duration',
#                                         value=datetime.timedelta(seconds=int(json_matches[i]['duration'])).__str__())
#                         embed.add_field(name='Game mod', value=config['GAME_MODS'][str(json_matches[i]['game_mode'])])
#                         embed.add_field(name='Result', value=result)


@bot.command(name='m')
async def get_emoji(ctx):
    pass


@bot.command(name='roll')
async def roll(ctx, start=1, end=100):
    roll_int = random.randint(start, end)
    await ctx.reply(str(roll_int))


async def get_heroes():
    current_time = time.time()
    if current_time - state.start_time > ONE_DAY or state.heroes is None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://api.opendota.com/api/herostats') as heroes_response:
                state.heroes = await heroes_response.json()
                state.start_time = time.time()
    else:
        pass


async def get_items():
    current_time = time.time()
    if current_time - state.start_time > ONE_DAY or state.items is None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.steampowered.com/IEconDOTA2_570/GetGameItems/V001/?key={os.environ["STEAM_API_KEY"]}&language=RU') as items_response:
                items = await items_response.json()
                state.items = items['result']['items']
                for item in state.items:
                    item['img'] = f'https://cdn.dota2.com/apps/dota2/images/items/{item["name"][5:]}_lg.png'
                state.start_time = time.time()
    else:
        pass


bot.run(os.environ['TOKEN'])
