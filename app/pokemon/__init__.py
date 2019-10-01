from bs4 import BeautifulSoup
import requests

from ..helpers import *
from . import data


def find(query):
    if check_vaild(query, '0123456789'):
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


def retreive_stats(dexNumber):
    url = 'https://pokemondb.net/pokedex/{}'.format(dexNumber)
    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    stats = soup.select('.tabs-panel.active>.grid-row')[1].select(
        '.grid-col>.resp-scroll>.vitals-table>tbody')[0].select('tr>td.cell-num')[::3]
    stats = list(map(lambda x: int(x.text), stats))
    return stats


class Pokemon:
    def __init__(self, dexnum: int, effort: list = [0]*6, individual: list = [31]*6, characteristic: tuple = (1, 1), level: int = 50):
        if dexnum > 0 and dexnum <= 809:
            self.dexnum = dexnum
            self.stat = retreive_stats(dexnum)
            self.setEffort(effort)
            self.setIndividual(individual)
            self.setCharacteristic(characteristic)
            self.setLevel(level)
        else:
            raise ValueError

    def setDexnum(self, dexnum: int):
        if dexnum > 0 and dexnum <= 809:
            self.dexnum = dexnum
            self.stat = retreive_stats(dexnum)
        else:
            raise ValueError

    def setEffort(self, effort: list):
        if sum(effort) <= 510 and max(effort) <= 252 and min(effort) >= 0:
            self.effort = effort
        else:
            raise ValueError

    def setIndividual(self, individual: list):
        if max(individual) <= 31 and min(individual) >= 0:
            self.individual = individual
        else:
            raise ValueError

    def setCharacteristic(self, characteristic: tuple):
        if max(characteristic) < 6 and min(characteristic) >= 1:
            self.characteristic = characteristic
        else:
            raise ValueError

    def setLevel(self, level: int):
        if level > 0 and level <= 100:
            self.level = level
        else:
            raise ValueError

    def actualStat(self):
        actualstat = list()
        actualstat.append(int((self.stat[0] * 2 + self.individual[0] +
                               self.effort[0] / 4) * (self.level / 100)) + 10 + self.level)
        for i in range(1, 6):
            appendstat = (self.stat[i] * 2 + self.individual[i]
                          + self.effort[i] / 4) * (self.level / 100) + 5
            if i == self.characteristic[0]:
                appendstat = int(appendstat * 1.1)
            elif i == self.characteristic[1]:
                appendstat = int(appendstat * 0.9)
            else:
                appendstat = int(appendstat)
            actualstat.append(appendstat)
        return actualstat
