from bot_script import client
import os

TOKEN = os.environ['DISCORD_TOKEN']

if __name__ == '__main__':
  client.run(TOKEN)
