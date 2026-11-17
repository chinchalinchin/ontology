**Guideline: Enums**

* All Enums used in the Application inherit from `StrEnum` or `IntEnum`.
* **Hot Loops** Because `StrEnum` is a `str` and `IntEnum` is an `int`, Python compares and hashes them directly in C without invoking the `Enum.value` descriptor. Do **not** add `.value` to Enum lookups. This has adverse effects on the Engine profile. 