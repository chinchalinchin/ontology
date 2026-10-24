**Guideline: Enums**

All enums are `class StringEnum(str, Enum)` or `class IntEnum(int, Enum)` mixins. Do not raise issues related to Enum `str` or `int` comparisons. 