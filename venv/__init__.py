# Work with Python 3.6
import discord
import asyncio
import pymongo
import os
from bson.objectid import ObjectId

mclient = pymongo.MongoClient("mongodb+srv://admin:{PASSWORD}@yellowlighten-wukhb.mongodb.net/test?retryWrites=true"
                             .format(PASSWORD=os.environ['MONGODB_TOKEN']))
client = discord.Client()
settings_db = mclient.settings



@client.event
async def on_message(message):

    async def snd_msg(__message):
        await client.send_message(message.channel, __message)

    if message.author == client.user:
        return

    if message.server.id not in settings_db.collection_names():
        prefix='yL'
    else:
        prefix=settings_db[message.server.id].find_one()['prefix']

    if not message.content.startswith(prefix):
        return

    parsedContent = message.content[len(prefix):]

    if parsedContent.startswith('config'):
        if message.server.id in settings_db.collection_names():
            await snd_msg("초기 설정은 이미 완료되었습니다.")
            return

        settings_db[message.server.id].insert_one({'prefix': 'yL', 'enabled': True})
        await snd_msg("yellowLighten을 사용할 준비가 되었습니다!!")
        return

    elif message.server.id not in settings_db.collection_names():
        await snd_msg("yellowLighten이 구성되지 않았습니다. 먼저 'yLconfig'를 입력해 주세요.")
        return

    elif not settings_db[message.server.id].find_one()['enabled']:
        if parsedContent.startswith('enable'):
            settings = settings_db[message.server.id].find_one()
            settings_id = settings['_id']
            settings.pop('_id', None)
            settings['enabled'] = True
            settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
            await snd_msg("yellowLighten이 활성화되었습니다!")
        return

    if parsedContent.startswith('prefix'):
        while (True):
            await snd_msg("봇을 부를 때 사용할 접두사(prefix)를 입력해 주세요. (취소는 현재 접두사 입력)")
            resp_1 = await client.wait_for_message(author=message.author)
            if resp_1.content == prefix:
                await snd_msg("접두사 설정이 취소되었습니다.")
                return

            await snd_msg("설정할 접두사가 '{}'이(가) 맞나요? (Y / N)".format(resp_1.content.strip()))

            def check(__message):
                return __message.content.startswith('Y') or __message.content.startswith('N')

            resp_2 = await client.wait_for_message(author=message.author, check=check)
            if resp_2.content.startswith('Y'):
                break

        settings = settings_db[message.server.id].find_one()
        settings_id = settings['_id']
        settings.pop('_id', None)
        settings['prefix'] = resp_1.content.strip()
        settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
        await snd_msg("접두사 설정이 완료되었습니다!")

    elif parsedContent.startswith('disable'):
        settings = settings_db[message.server.id].find_one()
        settings_id = settings['_id']
        settings.pop('_id', None)
        settings['enabled'] = False
        settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
        await snd_msg("yellowLighten이 비활성화되었습니다 ㅜㅜ")

    elif parsedContent.startswith('hello'):
        await snd_msg('{0.author.mention}님 안녕하세요!!'.format(message))

    elif parsedContent.startswith('square'):
        msg_get=parsedContent.split()
        if len(msg_get) != 2:
            msg = '잘못된 입력입니다'
        else:
            try:
                msg = '{}의 제곱은 {}입니다.'.format(int(msg_get[1]),int(msg_get[1])**2)
            except ValueError:
                msg = '잘못된 입력입니다'
        await snd_msg(msg)

    elif parsedContent.startswith('calc'):
        msg_get=parsedContent.split(' ', 1)
        if len(msg_get) < 2:
            msg = '잘못된 입력입니다'
        else:
            flg=True
            for i in msg_get[1]:
                if i not in '0123456789+-x^/()':
                    flg = False
            if not flg:
                msg = '잘못된 입력입니다'
            else:
                msg = '계산 결과: {}'.format(eval(msg_get[1].replace('x', '*').replace('^', '**')))
        await snd_msg(msg)

    else:
        await snd_msg('없는 명령어에요 ㅜㅜ 명령어 리스트는 {}help를 통해 확인해 주세요!'.format(prefix))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')