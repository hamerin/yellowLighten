# Work with Python 3.6
import discord
import asyncio
import pymongo
import os
import copy
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

    async def snd_msg(__message, __description=None):
        await client.send_message(message.channel, embed=discord.Embed(title=__message, description=__description, colour=color))

    async def snd_embed(__embed):
        await client.send_message(message.channel, embed=__embed)

    async def snd_text(__text):
        await client.send_message(message.channel, __text)

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
            await snd_msg("초기 설정은 이미 완료되었습니다.")
            return

        enable_dict = {channel.id: True for channel in message.server.channels}
        settings_db[message.server.id].insert_one({'prefix': 'yL',
                                                   'enabled': enable_dict,
                                                   'color': 0xfedb00})
        await snd_msg("설정 완료", "yellowLighten을 사용할 준비가 되었습니다!!")
        return

    elif message.server.id not in settings_db.collection_names():
        await snd_msg("yellowLighten이 구성되지 않았습니다. 먼저 `yLconfig` 를 입력해 주세요.")
        return

    elif not _settings['enabled'][message.channel.id]:
        if command == 'enable':
            settings = copy.deepcopy(_settings)
            settings_id = settings['_id']
            settings.pop('_id', None)
            settings['enabled'][message.channel.id] = True
            settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
            await snd_msg("yellowLighten이 **{}** 채널에서 활성화되었습니다!".format(message.channel.name))
        return

    if command == 'prefix':
        while (True):
            await snd_msg("봇을 부를 때 사용할 접두사(prefix)를 입력해 주세요. (취소는 현재 접두사 입력)")
            resp_1 = await client.wait_for_message(author=message.author)
            if resp_1.content == prefix:
                await snd_msg("접두사 설정이 취소되었습니다.")
                return

            await snd_msg("설정할 접두사가 **{}** 이(가) 맞나요? (Y / N)".format(resp_1.content.strip()))

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
            msg = '잘못된 입력입니다'
            await snd_msg(msg)
            return
        elif not len(msg_get[1]) == 6:
            msg = '잘못된 입력입니다'
            await snd_msg(msg)
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
            msg = '잘못된 입력입니다'
            await snd_msg(msg)
            return

    elif command == 'disable':
        settings = copy.deepcopy(_settings)
        settings_id = settings['_id']
        settings.pop('_id', None)
        settings['enabled'][message.channel.id] = False
        settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
        await snd_msg("yellowLighten이 **{}** 채널에서 비활성화되었습니다 ㅜㅜ".format(message.channel.name))

    elif command == 'hello':
        await snd_msg('**{}**님 안녕하세요!!'.format(message.author.name))

    elif command == 'bye':
        await snd_msg('**{}**님 안녕히가세요...'.format(message.author.name))

    elif command == 'calc':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
        else:
            try:
                flg = True
                for i in msg_get[1]:
                    if i not in '0123456789+-x^/()':
                        flg = False
                if not flg:
                    msg = '잘못된 입력입니다. 0123456789+-x^/()만 포함될 수 있습니다.'
                else:
                    msg = '계산 결과: **{}**'.format(eval(msg_get[1].replace('x', '*').replace('^', '**')))
            except SyntaxError:
                msg = '잘못된 입력입니다'
        await snd_msg(msg)

    elif command == 'factor':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
        else:
            flg = True
            for i in msg_get[1]:
                if i not in '0123456789':
                    flg = False
            if not flg:
                msg = '잘못된 입력입니다. 2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.'
            else:
                num = int(msg_get[1])
                if num > 10 ** 7 or num < 2:
                    msg = '잘못된 입력입니다. 2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.'
                else:
                    factor_dict = {}
                    for factor in factorize(num):
                        if factor in factor_dict:
                            factor_dict[factor] += 1
                        else:
                            factor_dict.update({factor: 1})
                    msg = "{} = **{}** 입니다.".format(num, ' x '.join([(str(key) if value == 1 else '{}^{}'.format(key, value)) for key, value in factor_dict.items()]))
        await snd_msg(msg)

    elif command == 'wiki':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
        else:
            msg = 'https://ko.wikipedia.org/wiki/{}'.format(msg_get[1].replace(' ', '_'))
        await snd_msg(msg)

    elif command == 'wiki-en':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
        else:
            msg = 'https://en.wikipedia.org/wiki/{}'.format(msg_get[1].replace(' ', '_'))
        await snd_msg(msg)

    elif command == 'namu':
        msg_get = parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
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