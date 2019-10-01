# Work with python 3.6
import discord
import asyncio
import pymongo
import os
import copy
import random
import requests
from bs4 import BeautifulSoup
from bson.objectid import ObjectId

from .helpers import *
from . import pokemon
from .error import CommandError

mongoClient = pymongo.MongoClient(
    f"mongodb+srv://admin:{os.environ['MONGODB_TOKEN']}@yellowlighten-wukhb.mongodb.net/test?retryWrites=true")
settingsDB = mongoClient.settings

client = discord.Client()


@client.event
async def on_message(message):
    async def send_embed(embed):
        await client.send_message(message.channel, embed=embed)

    async def send_message(message, description=None, author=None, author_url=None):
        embed = discord.Embed(title=message,
                              description=description,
                              colour=color)
        if author:
            if author_url:
                embed.set_author(name=author, icon_url=author_url)
            else:
                embed.set_author(name=author)

        await send_embed(embed)

    async def raise_error(description=None, title="잘못된 입력입니다."):
        await send_message(title, description)

    # Terminate if the message is belong to the bot
    if message.author == client.user:
        return

    # Define local variables
    serverSettings = settingsDB[message.server.id].find_one()
    serverSettingsID = {'_id': serverSettings['_id']}

    if message.server.id not in settingsDB.collection_names():
        prefix = 'yl '
        color = 0xfedb00
    else:
        prefix = serverSettings['prefix']
        color = serverSettings['color']

    if not message.content.startswith(prefix):
        return

    parsedContent = message.content[len(prefix):]
    command = parsedContent.split()[0]
    actualContent = None if len(parsedContent.split(
        ' ', 1)) < 2 else parsedContent.split(' ', 1)[1]

    # Commands
    if command == 'config':
        if message.server.id in settingsDB.collection_names():
            await send_message("초기 설정", "초기 설정은 이미 완료되었습니다.")
            return

        # Enable for all channels
        settingsDB[message.server.id].insert_one({'prefix': 'yL',
                                                  'enabled': {channel.id: True for channel in message.server.channels},
                                                  'color': 0xfedb00})

        await send_message("설정 완료", "yellowLighten을 사용할 준비가 되었습니다!!")
        return

    elif message.server.id not in settingsDB.collection_names():
        await send_message("초기 설정 필요", "yellowLighten이 구성되지 않았습니다. 먼저 `yLconfig` 를 입력해 주세요.")
        return

    elif not serverSettings['enabled'][message.channel.id]:
        if not command == 'enable':
            return

        settingsDB[message.server.id].update(
            serverSettingsID, {"$set": {f"enabled.{message.channel.id}": True}})
        await send_message("채널 활성화", "yellowLighten이 **{}** 채널에서 활성화되었습니다!".format(message.channel.name))
        return

    if command == 'prefix':
        while (True):
            def check(message):
                return message.content == 'Y' or message.content == 'N'

            await send_message("접두사 설정", "봇을 부를 때 사용할 접두사(prefix)를 입력해 주세요. (취소는 현재 접두사 입력)")

            resp1 = await client.wait_for_message(author=message.author)
            if resp1.content == prefix.strip():
                await send_message("접두사 설정", "접두사 설정이 취소되었습니다.")
                return

            await send_message("접두사 설정", "접두사 뒤 공백을 포함할까요? (Y / N)")

            resp2 = await client.wait_for_message(author=message.author, check=check)
            containBlank = (resp2.content == 'Y')
            prefixChanged = resp1.content.strip() + (' ' if containBlank else '')

            await send_message("접두사 설정", "설정할 접두사가 [**{}**] 이(가) 맞나요? (Y / N)".format(prefixChanged))

            resp3 = await client.wait_for_message(author=message.author, check=check)
            if resp3.content == 'Y':
                break

        settingsDB[message.server.id].update(
            serverSettingsID, {"$set": {"prefix": prefixChanged}})
        await send_message("접두사 설정 완료", "접두사가 [**{}**]로 재설정되었습니다.".format(prefixChanged))

    elif command == 'color':
        try:
            if not actualContent:
                raise CommandError
            if not len(actualContent) == 6:
                raise CommandError('색은 6자리의 16진수로 이루어져야 합니다')

            if actualContent == 'random':
                changedColor = random.randint(0x000000, 0xffffff)
            else:
                changedColor = int(actualContent, 16)

            settingsDB[message.server.id].update(
                serverSettingsID, {'$set': {'color': changedColor}})

            await send_embed(
                discord.Embed(title="색 설정 완료",
                              colour=changedColor))

        except CommandError as e:
            await raise_error(e.message)

        except SyntaxError:
            await raise_error()

    elif command == 'disable':
        settingsDB[message.server.id].update(
            serverSettingsID, {"$set": {f"enabled.{message.channel.id}": False}})
        await send_message("채널 비활성화", "yellowLighten이 **{}** 채널에서 비활성화되었습니다 ㅜㅜ".format(message.channel.name))

    elif command == 'hello':
        await send_message('**{}**님 안녕하세요!!'.format(message.author.name))

    elif command == 'bye':
        await send_message('**{}**님 안녕히가세요...'.format(message.author.name))

    elif command == 'calc':
        try:
            if not actualContent:
                raise CommandError
            if not check_vaild(actualContent, '0123456789+-x^/()'):
                raise CommandError('0123456789+-x^/()만 포함될 수 있습니다.')

            sendingMessage = '{}'.format(
                eval(actualContent.replace('x', '*').replace('^', '**')))
            await send_message("계산 결과", sendingMessage)

        except CommandError as e:
            await raise_error(e.message)

        except SyntaxError:
            await raise_error()

    elif command == 'factor':
        try:
            if not actualContent:
                raise CommandError
            if not check_vaild(actualContent, '0123456789+-x^/()'):
                raise CommandError('0123456789+-x^/()만 포함될 수 있습니다.')

            num = int(actualContent)
            if num > 10 ** 7 or num < 2:
                raise CommandError('2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.')

            factor_dict = {}
            for factor in factorize(num):
                if factor in factor_dict:
                    factor_dict[factor] += 1
                else:
                    factor_dict.update({factor: 1})

            sendingMessage = "{}".format(' x '.join([(str(key) if value == 1 else '{}^{}'.format(
                key, value)) for key, value in factor_dict.items()]))
            await send_message("소인수분해 결과", sendingMessage)

        except CommandError as e:
            await raise_error(e.message)

    elif command in ('wiki', 'wiki-ko'):
        faviconURL = "https://store-images.s-microsoft.com/image/apps.41885.9007199266246789.b5c9bced-c132-42c7-b8d5-8ae95a968b20.9605e2c4-06d4-46b9-8cfc-2e430b5bcab0"
        try:
            if not actualContent:
                raise CommandError

            url = 'https://ko.wikipedia.org/wiki/{}'.format(
                actualContent.replace(' ', '_'))
            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select('h1#firstHeading')[0].text
            desc = soup.select(
                'div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url

            await send_message(title, desc, "Wikipedia-ko", faviconURL)

        except CommandError as e:
            await raise_error(e.message)

        except IndexError:
            await send_message(None, "없는 문서입니다!", "Wikipedia-ko", faviconURL)

    elif command == 'wiki-en':
        faviconURL = "https://store-images.s-microsoft.com/image/apps.41885.9007199266246789.b5c9bced-c132-42c7-b8d5-8ae95a968b20.9605e2c4-06d4-46b9-8cfc-2e430b5bcab0"
        try:
            if not actualContent:
                raise CommandError

            url = 'https://en.wikipedia.org/wiki/{}'.format(
                actualContent.replace(' ', '_'))
            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select('h1#firstHeading')[0].text
            desc = soup.select(
                'div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url

            await send_message(title, desc, "Wikipedia-en", faviconURL)

        except CommandError as e:
            await raise_error(e.message)

        except IndexError:
            await send_message(None, "없는 문서입니다!", "Wikipedia-en", faviconURL)

    elif command in ('boj', 'baekjoon'):
        faviconURL = "https://pbs.twimg.com/profile_images/804340136259428353/fZud08Ao_400x400.jpg"

        try:
            if not actualContent:
                raise CommandError
            if not check_vaild(actualContent, '0123456789'):
                raise CommandError('문제 번호는 정수여야 합니다.')

            url = 'https://www.acmicpc.net/problem/{}'.format(
                actualContent)
            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select('title')[0].text
            difficulty = difficultyToString(int(requests.get(
                f'https://api.solved.ac/problem_level.php?id={title.split("번")[0]}').json()['level']))
            desc = soup.select('#problem_description')[0].text[1:-1]
            inp = soup.select('#problem_input')[0].text[1:-1]
            outp = soup.select('#problem_output')[0].text[1:-1]

            embed = discord.Embed(title=title + f' ({difficulty})',
                                  colour=color)
            embed.set_author(name="Baekjoon Online Judge",
                             icon_url=faviconURL)
            embed.add_field(name="문제", value=desc, inline=False)
            embed.add_field(name="입력", value=inp, inline=False)
            embed.add_field(name="출력", value=outp + '\n\n' + url, inline=False)
            await send_embed(embed)

        except CommandError as e:
            await raise_error(e.message)

        except IndexError:
            await send_message(None, "없는 문제입니다!", "Baekjoon Online Judge", faviconURL)

    elif command == 'neko':
        faviconURL = "https://avatars2.githubusercontent.com/u/34457007?s=200&v=4"
        image_url = requests.get(
            "https://nekos.life/api/v2/img/neko").json()['url']

        embed = discord.Embed(colour=color)
        embed.set_author(name="nekos.life",
                         icon_url=faviconURL)
        embed.set_image(url=image_url)
        await send_embed(embed)

    elif command in ('pokemon', 'poke'):
        try:
            if not actualContent:
                raise CommandError("포켓몬의 영어 이름, 한글 이름 또는 전국도감 번호를 입력해 주세요.")

            findResponse = pokemon.find(actualContent)
            if not findResponse[0]:
                raise CommandError("없는 포켓몬입니다.")

            await send_message("찾기 결과", '{}'.format(findResponse[1]))

        except CommandError as e:
            await raise_error(e.message)

    else:
        await send_message("없는 명령어", '명령어 리스트는 `{}help` 를 통해 확인해 주세요!'.format(prefix))


@client.event
async def on_channel_create(channel):
    serverSettingsID = {'_id': settingsDB[channel.server.id].find_one()['_id']}
    settingsDB[channel.server.id].update(
        serverSettingsID, {"$set": {f"enabled.{channel.id}": True}})


@client.event
async def on_channel_delete(channel):
    serverSettingsID = {'_id': settingsDB[channel.server.id].find_one()['_id']}
    settingsDB[channel.server.id].update(
        serverSettingsID, {"$unset": {f"enabled.{channel.id}": False}})


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
