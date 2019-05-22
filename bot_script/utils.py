def check_vaild(__str, __allowed):
  _flg = True
  for i in __str:
    if i not in __allowed:
      _flg = False
  return _flg
