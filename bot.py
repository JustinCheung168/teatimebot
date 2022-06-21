import os
import discord
from discord.embeds import _EmptyEmbed
from dotenv import load_dotenv


import dataframe_image as dfi
import random


import numpy as np
import pandas as pd

import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#to-do: figure out how to get this automatically
user_id_dict = {
    "armadillo":    279870739451084800,
    "beetknee":     376970858859593728,
    "Chaosfnog":    88020501930209280,
    "gazinobot":    978030120734445628,
    "jdub":         178957301485535232,
    "Josh":         178957301485535232,
    "klutz":        657683377725636619,
    "lilabeth":     469706380220170240,
    "firemike":     138336085703917568,
    "mikes fargo":  138336085703917568,
    "Mudae":        432610292342587392,
    "Pinscher":     202600215255973888,
    "HarvZh":       251112534231220225,
    "superharvey":  251112534231220225,
    "teatimebot":   988636031597309983
}
reverse_user_id_dict = {y: x for x, y in user_id_dict.items()}

client = discord.Client()

class TeaTimeBot():
    def __init__(self):
        self.highscoreboard = HighscoreBoard()
        self.scoreboards = {} #dict of dicts; keys are channels ids, second keys are users, values are scores
        self.activegames = {} #dict; keys are channels ids, values are either string of game name or None
        self.currentplayer = {} #dict; keys are channels ids, values are either string of player name or None
        self.highscorers = {} #dict; keys are channels ids, values are either list of player names or None

class CachedObject():
    def __init__(self, cache_path, default_object = None):
        self.cache_path = cache_path
        if os.path.exists(cache_path):
            self.local_object = json.load(open(self.cache_path, 'r'))
        else:
            self.local_object = default_object
    
    def update(self, new_object):
        self.local_object = new_object
        json.dump(self.local_object, open(self.cache_path, 'w'))

class HighscoreBoard(CachedObject):
    """
    Structure of local_object:
    {game:{player:score}}
    """
    def __init__(self, cache_path = "data/hs.json"):
        super().__init__(cache_path, default_object = {})

    def display(self, game):
        game_hsb = self.local_object[game]
        game_hsb_dict = {reverse_user_id_dict[int(key)]:[game_hsb[key]] for key in game_hsb.keys()}
        return pd.DataFrame(game_hsb_dict,index=['High Score']).T.sort_values(by='High Score', ascending = False)

    def set_score(self, game, player, new_score):

        player = str(player)

        if game not in self.local_object.keys():
            self.local_object[game] = {}

        if player not in self.local_object[game].keys():
            self.local_object[game][player] = 0

        if new_score > self.local_object[game][player]:
            self.local_object[game][player] = new_score
            json.dump(self.local_object, open(self.cache_path, 'w'))
            return True
        else:
            return False

    def get_score(self, game, player):
        return self.local_object[game][player]
    
ttb = TeaTimeBot()

@client.event
async def on_ready():
    """
    Runs on bot startup and lets us know which servers the bot successfully connected to.
    """
    print(f'{client.user} is connected to Discord!')
    for guild in client.guilds:
        print(f'Connected to {guild.name} (id: {guild.id})')

@client.event
async def on_message(message):
    """
    Runs every time any message is sent. Handles responses to messages.
    """
    channel = client.get_channel(message.channel.id)

    if message.author == client.user: #Immediately leave if this bot sent the message to prevent responses of bot to itself.
        return


    #Process commands:
    if (message.content[0:9] == "$hostecho") and (message.author.id == user_id_dict["klutz"]):
        await channel.send("Hi host!")

    if (message.content[0:10] == "$guestecho"):
        await channel.send(f"Hi {reverse_user_id_dict[int(message.author.id)]}!")

    if (message.content[0:6] == '$getid'):
        arg = message.content[7:]
        if arg in user_id_dict.keys():
            await channel.send(str(user_id_dict[arg]))
        elif len(arg) == 0:
            await channel.send("Please write someone's Discord name after $getid! For example:\n$getid klutz")
        else:
            await channel.send("Can't find that person!")

    if (message.content[0:11] == '$highscores'):
        arg = message.content[12:]

        if arg in ttb.highscoreboard.local_object.keys():
            ri = random.randrange(1000000,2000000)
            dfi.export(ttb.highscoreboard.display(arg),f"{ri}.png")
            await channel.send(file=discord.File(f"{ri}.png"))

        elif len(arg) == 0:
            await channel.send("Please write the name of a Mudae game after $highscores! For example:\n$highscores blacktea")
        else:
            await channel.send("I don't know that game!")





    if (message.content[0:9] == '$exitgame'):
        ttb.scoreboards[channel.id] = {}
        ttb.activegames[channel.id] = None
        ttb.highscorers[channel.id] = set()


    if (message.content[0:9] == '$teadebug'):
        print(ttb.scoreboards)
        print('test')





    if (message.author.id == user_id_dict["Mudae"]):

        
        #Tea Games!

        #greentea peripherals
        # if ("The Green Teaword will start!" in message.content):
        #     ttb.scoreboards
        # if (":tea: Quickly type a word containing:" in message.content):
        #     print('tea!')

        #blacktea peripherals
        if (len(message.embeds) > 0):
            embedded = message.embeds[0]
            if not isinstance(embedded.title, _EmptyEmbed):
                if ("The Black Teaword will start!" in embedded.title):
                    ttb.scoreboards[channel.id] = {}
                    ttb.activegames[channel.id] = "blacktea"
                    ttb.highscorers[channel.id] = set()

        if ((":coffee:" in message.content) and ("Type a word containing:" in message.content)): #given a prompt
            target_player = message.mentions[0].id
            ttb.currentplayer[channel.id] = target_player
            if target_player not in ttb.scoreboards[channel.id].keys():
                ttb.scoreboards[channel.id][target_player] = 1
            else:
                ttb.scoreboards[channel.id][target_player] += 1

        if (":boom: Time's up:" in message.content): #question wrong
            target_player = ttb.currentplayer[channel.id]
            ttb.scoreboards[channel.id][target_player] -= 1
            record_beaten = ttb.highscoreboard.set_score(ttb.activegames[channel.id], target_player, ttb.scoreboards[channel.id][target_player])
            if record_beaten:
                ttb.highscorers[channel.id].add(target_player)

        if ((":trophy::trophy::trophy:" in message.content) and ("won the game!" in message.content)):
            for highscorer in ttb.highscorers[channel.id]:
                await channel.send("⭐ HIGH SCORE! ⭐\n"+reverse_user_id_dict[highscorer]+": "+str(ttb.highscoreboard.get_score(ttb.activegames[channel.id],highscorer)))
            ttb.highscorers[channel.id]=set()

        if ("No participants..." in message.content):
            ttb.activegames[channel] = None





client.run(TOKEN)