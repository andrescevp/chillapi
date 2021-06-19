class ConfigError(Exception):
    """Exception raised for errors in the config."""

    def __init__(self, message):
        self.message = message


class TableNotExist(ConfigError):
    """ """

    pass


class ColumnNotExist(ConfigError):
    """ """

    pass


class RuntimeException(ConfigError):
    """ """

    pass


class LogicException(ConfigError):
    """ """

    pass


class ResourceArgumentsLogicException(ConfigError):
    """ """

    pass
