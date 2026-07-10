from abc import ABC, abstractmethod

from src.domain.value_objects.short_code_value_object import ShortCode


class ShortCodeGenerator(ABC):
    """Short code generator interface."""

    @abstractmethod
    async def generate(self) -> ShortCode:
        """Generate short code."""
        ...
