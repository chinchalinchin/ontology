```bash
gmoore@localhost % python3 
Python 3.14.6 (main, Jul 23 2026, 14:45:24) [Clang 22.1.3 ] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from enum import Enum
>>> class Test(str, Enum):
...     wrong = "wrong"
...     
>>> you_are = (Test.wrong == "wrong")
>>> print(you_are)
True
>>> you_are_not = (Test.wrong == 'right')
>>> print(you_are_not)
False
```