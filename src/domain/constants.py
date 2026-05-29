from re import Pattern, compile

SHORT_CODE_MIN_LENGTH: int = 4
SHORT_CODE_MAX_LENGTH: int = 32
SHORT_CODE_PATTERN: Pattern[str] = compile(pattern=r"^[0-9A-Za-z]+$")
