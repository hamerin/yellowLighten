# Work with Python 3.6
import discord
import asyncio
import pymongo
import os

mclient = pymongo.MongoClient("mongodb+srv://admin:{PASSWORD}@yellowlighten-wukhb.mongodb.net/test?retryWrites=true"
                             .format(PASSWORD=os.environ['MONGODB_TOKEN']))
client = discord.Client()
settings_db = mclient.settings


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        settings_db[message.server.id].insert_one({'prefix': '!'})
        await client.send_message(message.channel, msg)
    if message.content.startswith('!square'):
        msg=''
        msg_get=message.content.split()
        if len(msg_get) != 2:
            msg='Input invaild'
        else:
            msg='Square of {num} is {sq}'.format(num=int(msg_get[1]), sq=int(msg_get[1])**2)
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')