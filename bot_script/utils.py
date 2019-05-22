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
