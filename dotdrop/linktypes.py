from enum import IntEnum


class LinkTypes(IntEnum):
    NOLINK = 0
    LINK = 1
    LINK_CHILDREN = 2

    @classmethod
    def get(cls, key, default=None):
        try:
            return key if isinstance(key, cls) else cls[key.upper()]
        except KeyError:
            if default:
                return default
            raise ValueError('bad {} value: "{}"'.format(cls.__name__, key))

    def __str__(self):
        return self.name.lower()
