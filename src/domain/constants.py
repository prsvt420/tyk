from typing import FrozenSet

SHORT_CODE_MIN_LENGTH: int = 4
SHORT_CODE_MAX_LENGTH: int = 32
SHORT_CODE_ALPHABET: str = (
    "0123456789" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz"
)
SHORT_CODE_ALLOWED_CHARS: FrozenSet[str] = frozenset(SHORT_CODE_ALPHABET)
