from typing import Any

from HABApp.openhab.items.base_item import OpenhabItem
from ..definitions import OpenClosedValue
from ...core.const import MISSING
from ..errors import SendCommandNotSupported


class ContactItem(OpenhabItem):
    """ContactItem

    :ivar str name:
    :ivar str value:

    :ivar Optional[str] label:
    :ivar FrozenSet[str] tags:
    :ivar FrozenSet[str] groups:
    :ivar Mapping[str, MetaData] metadata:
    """

    def set_value(self, new_value) -> bool:

        if isinstance(new_value, OpenClosedValue):
            new_value = new_value.value

        if new_value is not None and new_value != OpenClosedValue.OPEN and new_value != OpenClosedValue.CLOSED:
            raise ValueError(f'Invalid value for ContactItem: {new_value}')
        return super().set_value(new_value)

    def is_open(self) -> bool:
        """Test value against open-value"""
        return self.value == OpenClosedValue.OPEN

    def is_closed(self) -> bool:
        """Test value against closed-value"""
        return self.value == OpenClosedValue.CLOSED

    def oh_send_command(self, value: Any = MISSING):
        raise SendCommandNotSupported(f'{self.__class__.__name__} does not support send command! '
                                      'See openHAB documentation for details.')

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, ContactItem):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        elif isinstance(other, int):
            if other and self.is_open():
                return True
            if not other and self.is_closed():
                return True
            return False

        return NotImplemented
