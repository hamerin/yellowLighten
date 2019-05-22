from . import utils
from . import data

def find(query):
  if utils.check_vaild(query, '0123456789'):
    qu = int(query)
  else:
    qu = ' '.join(map(str.capitalize, query.split()))

  dex_num = -1
  for i in data.pokemon_name_data:
    if qu in i:
      dex_num = i[0]
  if dex_num == -1:
    return (False, dex_num)
  else:
    return (True, dex_num)

def retreive_info(dexNumber):
  
