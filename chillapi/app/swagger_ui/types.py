"Some extended types for more comprehensive parameter annotations"

import io


class listof(list):
    "Dummy class representing typed lists"

    def __init__(self, subtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtype = subtype


class file(io.IOBase):
    "Dummy class representing a file"
    pass


class enum:
    "Enumerate class that will contain the given elements"

    def __init__(self, *args, **kwargs):
        self.__entry_dict = {}
        self.__consume_list(args)
        self.__consume_dict(kwargs)
        for key, value in self.__entry_dict.items():
            setattr(self, key, value)

        def unique_len(x):
            "Counts number of unique elements in the given iterable"
            return len(list(set(x)))

        assert unique_len(self.__entry_dict.values()) == len(self.__entry_dict), "Values for enum items must be unique."

    def __consume_list(self, values):
        "Consumes the list of strings as the enumeration titles"

        entry_dict = {}
        for index, name in enumerate(values):
            assert type(name) == str, "The input list to enum class must contain strings only (got `{}:{}`)".format(name, type(name))
            entry_dict[name] = index
        self.__entry_dict.update(entry_dict)

    def __consume_dict(self, values):
        "Consumes the dictionary of strings to integers as the enumeration titles"

        for name, index in values.items():
            assert type(name) == str, "The input dict to enum class must contain a map from strings to integers only (got `key={}:{}`)".format(
                name, type(name)
            )
            assert type(index) == int, "The input dict to enum class must contain a map from strings to integers only (got `val={}:{}`)".format(
                index, type(index)
            )
        self.__entry_dict.update(values)

    @property
    def entries(self):
        "Returns the items inside this enum"

        return self.__entry_dict.copy()


def crepr(class_):
    "Creates a convertible representation for the given type"

    if isinstance(class_, enum):
        return "enum({})".format(", ".join([f"{k}={v}" for k, v in class_.entries]))
    elif issubclass(class_, file):
        return "file"
    elif isinstance(class_, listof):
        return "listof({})".format(crepr(class_.subtype))
    elif isinstance(class_, type):
        return class_.__name__
    raise RuntimeError("Input to crepr must be a type.")
