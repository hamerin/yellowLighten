# Work with Python 3.6
import discord
import asyncio
import pymongo
import os
import copy
import requests
from bs4 import BeautifulSoup
from bson.objectid import ObjectId

mclient = pymongo.MongoClient("mongodb+srv://admin:{PASSWORD}@yellowlighten-wukhb.mongodb.net/test?retryWrites=true"
                             .format(PASSWORD=os.environ['MONGODB_TOKEN']))
client = discord.Client()
settings_db = mclient.settings

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    _settings = settings_db[message.server.id].find_one()

    if message.server.id not in settings_db.collection_names():
        prefix = 'yL'
        color = 0xfedb00
    else:
        prefix = _settings['prefix']
        color = _settings['color']

    if not message.content.startswith(prefix):
        return

    async def snd_embed(__embed):
        await client.send_message(message.channel, embed=__embed)

    async def snd_msg(__message, __description=None, __author=None, __author_url=None):
        _embed = discord.Embed(title=__message,
                               description=__description,
                               colour=color)
        if __author:
            if __author_url:
                _embed.set_author(name=__author, icon_url=__author_url)
            else:
                _embed.set_author(name=__author)

        await snd_embed(_embed)

    async def snd_text(__text):
        await client.send_message(message.channel, __text)

    async def raise_err(__description=None, __title="잘못된 입력입니다."):
        await snd_msg(__title, __description)

    def check_vaild(__str, __allowed):
        _flg = True
        for i in __str:
            if i not in __allowed:
                _flg = False
        return _flg

    def factorize(n):
        while n > 1:
            for i in range(2, n + 1):
                if n % i == 0:
                    n //= i
                    yield i
                    break

    parsedContent = message.content[len(prefix):]
    command = parsedContent.split()[0]

    if command == 'config':
        if message.server.id in settings_db.collection_names():
            await snd_msg("초기 설정", "초기 설정은 이미 완료되었습니다.")
            return

        enable_dict = {channel.id: True for channel in message.server.channels}
        settings_db[message.server.id].insert_one({'prefix': 'yL',
                                                   'enabled': enable_dict,
                                                   'color': 0xfedb00})
        await snd_msg("설정 완료", "yellowLighten을 사용할 준비가 되었습니다!!")
        return

    elif message.server.id not in settings_db.collection_names():
        await snd_msg("초기 설정 필요", "yellowLighten이 구성되지 않았습니다. 먼저 `yLconfig` 를 입력해 주세요.")
        return

    elif not _settings['enabled'][message.channel.id]:
        if command == 'enable':
            settings = copy.deepcopy(_settings)
            settings_id = settings['_id']
            settings.pop('_id', None)
            settings['enabled'][message.channel.id] = True
            settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
            await snd_msg("채널 활성화", "yellowLighten이 **{}** 채널에서 활성화되었습니다!".format(message.channel.name))
        return

    if command == 'prefix':
        while (True):
            await snd_msg("접두사 설정", "봇을 부를 때 사용할 접두사(prefix)를 입력해 주세요. (취소는 현재 접두사 입력)")
            resp_1 = await client.wait_for_message(author=message.author)
            if resp_1.content == prefix:
                await snd_msg("접두사 설정", "접두사 설정이 취소되었습니다.")
                return

            await snd_msg("접두사 설정", "설정할 접두사가 **{}** 이(가) 맞나요? (Y / N)".format(resp_1.content.strip()))

            def check(__message):
                return __message.content == 'Y' or __message.content == 'N'

            resp_2 = await client.wait_for_message(author=message.author, check=check)
            if resp_2.content == 'Y':
                break

        settings = copy.deepcopy(_settings)
        settings_id = settings['_id']
        settings.pop('_id', None)
        settings['prefix'] = resp_1.content.strip()
        settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
        await snd_msg("접두사 설정 완료", "접두사가 **{}**로 재설정되었습니다.".format(resp_1.content.strip()))

    elif command == 'color':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        elif not len(msg_get[1]) == 6:
            await raise_err()
            return
        try:
            __color = int(msg_get[1], 16)

            settings = copy.deepcopy(_settings)
            settings_id = settings['_id']
            settings.pop('_id', None)
            settings['color'] = __color
            settings_db[message.server.id].replace_one({'_id': settings_id}, settings)

            await snd_embed(
                discord.Embed(title="색 설정 완료",
                              colour=__color))
        except SyntaxError:
            await raise_err()
            return

    elif command == 'disable':
        settings = copy.deepcopy(_settings)
        settings_id = settings['_id']
        settings.pop('_id', None)
        settings['enabled'][message.channel.id] = False
        settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
        await snd_msg("채널 비활성화", "yellowLighten이 **{}** 채널에서 비활성화되었습니다 ㅜㅜ".format(message.channel.name))

    elif command == 'hello':
        await snd_msg('**{}**님 안녕하세요!!'.format(message.author.name))

    elif command == 'bye':
        await snd_msg('**{}**님 안녕히가세요...'.format(message.author.name))

    elif command == 'calc':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        else:
            try:
                if not check_vaild(msg_get[1], '0123456789+-x^/()'):
                    await raise_err('0123456789+-x^/()만 포함될 수 있습니다.')
                    return
                else:
                    msg = '{}'.format(eval(msg_get[1].replace('x', '*').replace('^', '**')))
            except SyntaxError:
                await raise_err()
                return
        await snd_msg("계산 결과", msg)

    elif command == 'factor':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        else:
            if not check_vaild(msg_get[1], '0123456789'):
                await raise_err('2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.')
                return
            else:
                num = int(msg_get[1])
                if num > 10 ** 7 or num < 2:
                    await raise_err('2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.')
                    return
                else:
                    factor_dict = {}
                    for factor in factorize(num):
                        if factor in factor_dict:
                            factor_dict[factor] += 1
                        else:
                            factor_dict.update({factor: 1})
                    msg = "{}".format(' x '.join([(str(key) if value == 1 else '{}^{}'.format(key, value)) for key, value in factor_dict.items()]))
        await snd_msg("소인수분해 결과", msg)

    elif command == 'wiki' or command == 'wiki-ko':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        else:
            try:
                url = 'https://ko.wikipedia.org/wiki/{}'.format(msg_get[1].replace(' ', '_'))
                req = requests.get(url)
                html = req.text
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.select('h1#firstHeading')[0].text
                desc = soup.select('div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url
            except IndexError:
                await snd_msg(None, "없는 문서입니다!", "Wikipedia-ko")
                return

        await snd_msg(title, desc, "Wikipedia-ko")

    elif command == 'wiki-en':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        else:
            try:
                url = 'https://en.wikipedia.org/wiki/{}'.format(msg_get[1].replace(' ', '_'))
                req = requests.get(url)
                html = req.text
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.select('h1#firstHeading')[0].text
                desc = soup.select('div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url
            except IndexError:
                await snd_msg(None, "없는 문서입니다!", "Wikipedia-en")
                return

        await snd_msg(title, desc, "Wikipedia-en")

    elif command == 'boj' or command == 'baekjoon':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        if not check_vaild(msg_get[1], '0123456789'):
            await raise_err('문제 번호는 정수여야 합니다.')
            return
        else:
            try:
                url = 'https://www.acmicpc.net/problem/{}'.format(msg_get[1])
                req = requests.get(url)
                html = req.text
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.select('title')[0].text
                desc = soup.select('#problem_description')[0].text[1:-1]
                inp = soup.select('#problem_input')[0].text[1:-1]
                outp = soup.select('#problem_output')[0].text[1:-1]
            except IndexError:
                await snd_msg(None, "없는 문제입니다!", "Baekjoon Online Judge")
                return

        embed = discord.Embed(title=title,
                              colour=color)
        embed.set_author(name="Baekjoon Online Judge")
        embed.add_field(name="문제", value=desc)
        embed.add_field(name="입력", value=inp)
        embed.add_field(name="출력", value=outp + '\n\n' + url)
        await snd_embed(embed)

    elif command == 'namu':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            await raise_err()
            return
        else:
            msg = 'https://namu.wiki/w/{}'.format(msg_get[1].replace(' ', '_'))
        await snd_msg(msg)

    else:
        await snd_msg('없는 명령어에요 ㅜㅜ 명령어 리스트는 `{}help` 를 통해 확인해 주세요!'.format(prefix))

@client.event
async def on_channel_create(channel):
    _settings = settings_db[channel.server.id].find_one()
    settings = copy.deepcopy(_settings)
    settings_id = settings['_id']
    settings.pop('_id', None)
    settings['enabled'].update({channel.id: True})
    settings_db[channel.server.id].replace_one({'_id': settings_id}, settings)

@client.event
async def on_channel_delete(channel):
    _settings = settings_db[channel.server.id].find_one()
    settings = copy.deepcopy(_settings)
    settings_id = settings['_id']
    settings.pop('_id', None)
    settings['enabled'].pop(channel.id, None)
    settings_db[channel.server.id].replace_one({'_id': settings_id}, settings)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')