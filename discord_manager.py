import discord
from discord import Intents
from discord.ext import commands
from discord.utils import get

from dotenv import load_dotenv

from pymongo import MongoClient

import os


load_dotenv()

intents = Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', description='DiscordManager', intents=intents)
database = MongoClient('mongodb+srv://<username>:{}@cluster0.1sdlk.mongodb.net/<project_name>?retryWrites=true&w=majority'.format(os.getenv('DATABASE_PASSWORD')))


### CLASSES ###
class Games:
    def __init__(self, database, game, id):
        self.database = database
        self.game = game
        self.id = id

    def add(self):
        if self.database.collectibles.games.count_documents({'id' : self.id}) > 0:
            self.database.collectibles.games.update_one({'id' : self.id}, {'$push' : {'games' : self.game}})
        else:
            self.database.collectibles.games.insert_one({'id' : self.id, 'games' : [self.game]})

    def remove(self):
        if self.database.collectibles.games.count_documents({'id' : self.id}) > 0:
            self.database.collectibles.games.update_one({'id' : self.id}, {'$pull' : {'games' : self.game}})


class Profile:
    def __init__(self, database, id, social, username):
        self.database = database
        self.id = id
        self.social = social
        self.username = username

    def add(self):
        if self.database.collectibles.profiles.count_documents({'id' : self.id}) > 0:
            self.database.collectibles.profiles.update_one({'id' : self.id}, {'$push' : {'usernames' : '{}:{}'.format(self.social, self.username)}})
        else:
            self.database.collectibles.profiles.insert_one({'id' : self.id, 'usernames' : ['{}:{}'.format(self.social, self.username)]})

    def remove(self):
        if self.database.collectibles.profiles.count_documents({'id' : self.id}) > 0:
            self.database.collectibles.profiles.update_one({'id' : self.id}, {'$pull' : {'usernames' : '{}:{}'.format(self.social, self.username)}})


### EVENTS ###
@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    if message.author.bot != True and ctx.valid:
        await bot.process_commands(message)

@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))


### COMMANDS ###
@bot.command()
async def add_game(ctx, code):
    if is_channel(ctx.channel.name, 'use-commands'):
        Games(database, get_name_from_code(code), ctx.message.author.id).add()
        await ctx.message.delete()

@bot.command()
async def remove_game(ctx, code):
    if is_channel(ctx.channel.name, 'use-commands'):
        Games(database, get_name_from_code(code), ctx.message.author.id).remove()
        await ctx.message.delete()

@bot.command()
async def games(ctx, member: discord.User=None):
    if is_channel(ctx.channel.name, 'use-commands'):
        dict = database.collectibles.games.find_one({'id' : member.id if member != None else ctx.message.author.id})
        await ctx.channel.send("**{}'s Catalogue**\n{}".format(member if member != None else ctx.message.author.name, '\n'.join(sorted(dict['games']))))
        await ctx.message.delete()

@bot.command()
async def socials(ctx, member: discord.User=None):
    if is_channel(ctx.channel.name, 'use-commands'):
        usernames = database.collectibles.profiles.find_one({'id' : member.id if member != None else ctx.message.author.id})['usernames']

        arr = []
        for key in sorted(usernames):
            arr.append('{}: @{}'.format(get_social_name_from_code(key.split(':')[0]).capitalize(), key.split(':')[1]))

        await ctx.channel.send("**{}'s Socials**\n{}".format(member if member != None else ctx.message.author.name, '\n'.join(arr)))
        await ctx.message.delete()

@bot.command()
async def codes(ctx):
    if is_channel(ctx.channel.name, 'use-commands'):
        for member in bot.get_all_members():
            if member.id == ctx.message.author.id:
                await bot.get_user(member.id).send('**Available Game Codes**\n{}\n\n**Available Social Codes**\n{}'.format(get_all_game_codes(), get_all_social_codes()))
                await ctx.message.delete()

@bot.command()
async def create_game_code(ctx, code, name):
    if is_channel(ctx.channel.name, 'manage-games'):
        database.collectibles.game_ids.insert_one({'code' : code, 'name' : name}) if database.collectibles.game_ids.count_documents({'code' : code}) == 0 else await ctx.channel.send('{} has already been added'.format(code))
        await ctx.message.delete()

@bot.command()
async def create_social_code(ctx, code, name):
    if is_channel(ctx.channel.name, 'manage-socials'):
        database.collectibles.platform_ids.insert_one({'code' : code, 'name' : name}) if database.collectibles.social_ids.count_documents({'code' : code}) == 0 else await ctx.channel.send('{} has already been added'.format(code))
        await ctx.message.delete()

@bot.command()
async def add_social(ctx, social, username):
    if is_channel(ctx.channel.name, 'use-commands'):
        Profile(database, ctx.message.author.id, social.lower(), username.lower()).add()
        await ctx.message.delete()

@bot.command()
async def remove_social(ctx, social, username):
    if is_channel(ctx.channel.name, 'use-commands'):
        Profile(database, ctx.message.author.id, social.lower(), username.lower()).remove()
        await ctx.message.delete()


def get_all_game_codes():
    ids = []
    game_ids = database.collectibles.game_ids.find({})
    for game_id in game_ids:
        ids.append("{}: ` {} `".format(get_name_from_code(game_id['code']), game_id['code']))

    return '\n'.join(sorted(ids))

def get_all_social_codes():
    ids = []
    social_ids = database.collectibles.platform_ids.find({})
    for social_id in social_ids:
        ids.append("{}: ` {} `".format(get_social_name_from_code(social_id['code']), social_id['code']))

    return '\n'.join(sorted(ids))


def get_name_from_code(code):
    return database.collectibles.game_ids.find_one({'code' : code})['name']

def get_social_name_from_code(code):
    return database.collectibles.platform_ids.find_one({'code' : code})['name']


def is_channel(name, channel):
    return True if name == channel else False


bot.run(os.getenv('TOKEN'))
