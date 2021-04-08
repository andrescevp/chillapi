class ConfigError(Exception):
    """Exception raised for errors in the config.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
