from venv import client
from boto.s3.connection import S3Connection
import os

s3 = S3Connection(os.environ['S3_KEY'], os.environ['S3_SECRET'])
TOKEN = ''

if __name__ == '__main__':
    client.run(TOKEN)