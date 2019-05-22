# Work with python 3.6
import discord
import asyncio
import pymongo
import os
import copy
import random
import requests
import nekos
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from . import pokemon
from . import utils

mclient = pymongo.MongoClient("mongodb+srv://admin:{PASSWORD}@yellowlighten-wukhb.mongodb.net/test?retryWrites=true"
                              .format(PASSWORD=os.environ['MONGODB_TOKEN']))
client = discord.Client()
settings_db = mclient.settings


@client.event
async def on_message(message):
  async def snd_embed(embed):
    await client.send_message(message.channel, embed=embed)

  async def snd_msg(message, description=None, author=None, author_url=None):
    embed = discord.Embed(title=message,
                          description=description,
                          colour=color)
    if author:
      if author_url:
        embed.set_author(name=author, icon_url=author_url)
      else:
        embed.set_author(name=author)

    await snd_embed(embed)

  async def snd_text(text):
    await client.send_message(message.channel, text)

  async def raise_err(description=None, title="잘못된 입력입니다."):
    await snd_msg(title, description)

  if message.author == client.user:
    return

  _settings = settings_db[message.server.id].find_one()

  if message.server.id not in settings_db.collection_names():
    prefix = 'yl '
    color = 0xfedb00
  else:
    prefix = _settings['prefix']
    color = _settings['color']

  if not message.content.startswith(prefix):
    return

  parsedContent = message.content[len(prefix):]
  command = parsedContent.split()[0]
  actualContent = None if len(parsedContent.split(
      ' ', 1)) < 2 else parsedContent.split(' ', 1)[1]

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
      settings_db[message.server.id].replace_one(
          {'_id': settings_id}, settings)
      await snd_msg("채널 활성화", "yellowLighten이 **{}** 채널에서 활성화되었습니다!".format(message.channel.name))
    return

  if command == 'prefix':
    while (True):
      await snd_msg("접두사 설정", "봇을 부를 때 사용할 접두사(prefix)를 입력해 주세요. (취소는 현재 접두사 입력)")
      resp_1 = await client.wait_for_message(author=message.author)
      if resp_1.content == prefix:
        await snd_msg("접두사 설정", "접두사 설정이 취소되었습니다.")
        return

      await snd_msg("접두사 설정", "접두사 뒤 공백을 포함할까요? (Y / N)")

      def check(__message):
        return __message.content == 'Y' or __message.content == 'N'

      resp_2 = await client.wait_for_message(author=message.author, check=check)
      containBlank = (resp_2.content == 'Y')
      prefixChanged = resp_1.content.strip() + ' ' if containBlank else None
      await snd_msg("접두사 설정", "설정할 접두사가 [**{}**] 이(가) 맞나요? (Y / N)".format(prefixChanged))

      resp_3 = await client.wait_for_message(author=message.author, check=check)
      if resp_3.content == 'Y':
        break

    settings = copy.deepcopy(_settings)
    settings_id = settings['_id']
    settings.pop('_id', None)
    settings['prefix'] = prefixChanged
    settings_db[message.server.id].replace_one({'_id': settings_id}, settings)
    await snd_msg("접두사 설정 완료", "접두사가 [**{}**]로 재설정되었습니다.".format(prefixChanged))
    return

  elif command == 'color':
    if not actualContent:
      await raise_err()
      return
    elif not len(actualContent) == 6:
      await raise_err()
      return
    try:
      if actualContent == 'random':
        changedColor = random.randint(0x000000, 0xffffff)
      else:
        changedColor = int(actualContent, 16)

      settings = copy.deepcopy(_settings)
      settings_id = settings['_id']
      settings.pop('_id', None)
      settings['color'] = changedColor
      settings_db[message.server.id].replace_one(
          {'_id': settings_id}, settings)

      await snd_embed(
          discord.Embed(title="색 설정 완료",
                        colour=changedColor))
      return

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
    return

  elif command == 'hello':
    await snd_msg('**{}**님 안녕하세요!!'.format(message.author.name))
    return

  elif command == 'bye':
    await snd_msg('**{}**님 안녕히가세요...'.format(message.author.name))
    return

  elif command == 'calc':
    if not actualContent:
      await raise_err()
      return
    else:
      try:
        if not utils.check_vaild(actualContent, '0123456789+-x^/()'):
          await raise_err('0123456789+-x^/()만 포함될 수 있습니다.')
          return
        else:
          sendingMessage = '{}'.format(
              eval(actualContent.replace('x', '*').replace('^', '**')))
      except SyntaxError:
        await raise_err()
        return
    await snd_msg("계산 결과", sendingMessage)
    return

  elif command == 'factor':
    if not actualContent:
      await raise_err()
      return
    else:
      if not utils.check_vaild(actualContent, '0123456789+-x^/()'):
        await raise_err('0123456789+-x^/()만 포함될 수 있습니다.')
        return
      else:
        num = int(actualContent)
        if num > 10 ** 7 or num < 2:
          await raise_err('2 이상 10000000 이하의 정수만 소인수분해할 수 있습니다.')
          return
        else:
          factor_dict = {}
          for factor in utils.factorize(num):
            if factor in factor_dict:
              factor_dict[factor] += 1
            else:
              factor_dict.update({factor: 1})
          sendingMessage = "{}".format(' x '.join([(str(key) if value == 1 else '{}^{}'.format(
              key, value)) for key, value in factor_dict.items()]))
    await snd_msg("소인수분해 결과", sendingMessage)
    return

  elif command in ('wiki', 'wiki-ko'):
    favicon_url = "https://store-images.s-microsoft.com/image/apps.41885.9007199266246789.b5c9bced-c132-42c7-b8d5-8ae95a968b20.9605e2c4-06d4-46b9-8cfc-2e430b5bcab0"
    if not actualContent:
      await raise_err()
      return
    else:
      try:
        url = 'https://ko.wikipedia.org/wiki/{}'.format(
            actualContent.replace(' ', '_'))
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.select('h1#firstHeading')[0].text
        desc = soup.select(
            'div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url
      except IndexError:
        await snd_msg(None, "없는 문서입니다!", "Wikipedia-ko", favicon_url)
        return

    await snd_msg(title, desc, "Wikipedia-ko", favicon_url)
    return

  elif command == 'wiki-en':
    favicon_url = "https://store-images.s-microsoft.com/image/apps.41885.9007199266246789.b5c9bced-c132-42c7-b8d5-8ae95a968b20.9605e2c4-06d4-46b9-8cfc-2e430b5bcab0"
    if not actualContent:
      await raise_err()
      return
    else:
      try:
        url = 'https://en.wikipedia.org/wiki/{}'.format(
            actualContent.replace(' ', '_'))
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.select('h1#firstHeading')[0].text
        desc = soup.select(
            'div.mw-parser-output > p:not(.mw-empty-elt)')[0].text[:-1] + '\n\n' + url
      except IndexError:
        await snd_msg(None, "없는 문서입니다!", "Wikipedia-en", favicon_url)
        return

    await snd_msg(title, desc, "Wikipedia-en", favicon_url)
    return

  elif command in ('boj', 'baekjoon'):
    favicon_url = "https://pbs.twimg.com/profile_images/804340136259428353/fZud08Ao_400x400.jpg"
    if not actualContent:
      await raise_err()
      return
    if not utils.check_vaild(actualContent, '0123456789'):
      await raise_err('문제 번호는 정수여야 합니다.')
      return
    else:
      try:
        url = 'https://www.acmicpc.net/problem/{}'.format(actualContent)
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.select('title')[0].text
        desc = soup.select('#problem_description')[0].text[1:-1]
        inp = soup.select('#problem_input')[0].text[1:-1]
        outp = soup.select('#problem_output')[0].text[1:-1]
      except IndexError:
        await snd_msg(None, "없는 문제입니다!", "Baekjoon Online Judge", favicon_url)
        return

    embed = discord.Embed(title=title,
                          colour=color)
    embed.set_author(name="Baekjoon Online Judge",
                     icon_url=favicon_url)
    embed.add_field(name="문제", value=desc, inline=False)
    embed.add_field(name="입력", value=inp, inline=False)
    embed.add_field(name="출력", value=outp + '\n\n' + url, inline=False)
    await snd_embed(embed)
    return

  elif command == 'neko':
    favicon_url = "https://avatars2.githubusercontent.com/u/34457007?s=200&v=4"
    image_url = nekos.img("neko")
    embed = discord.Embed(colour=color)
    embed.set_author(name="nekos.life",
                     icon_url=favicon_url)
    embed.set_image(url=image_url)
    await snd_embed(embed)
    return

  elif command in ('pokedex', 'poke'):
    if not actualContent:
      await raise_err("포켓몬의 영어 이름, 한글 이름 또는 전국도감 번호를 입력해 주세요.")
      return

    findResponse = pokemon.find(actualContent)
    if not findResponse[0]:
      await raise_err("없는 포켓몬입니다.")
      return
    else:
      await snd_msg("찾기 결과", '{}'.format(findResponse[1]))
      return

  else:
    await snd_msg("없는 명령어", '명령어 리스트는 `{}help` 를 통해 확인해 주세요!'.format(prefix))
    return


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
