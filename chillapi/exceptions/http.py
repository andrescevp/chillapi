from werkzeug.exceptions import HTTPException


class NotFoundException(HTTPException):
    """ """

    code = 404
    description = "Not Found"


class RequestSchemaError(HTTPException):
    """ """

    code = 400
    description = "Request body invalid"


class RequestInvalidFieldSchemaError(HTTPException):
    """ """

    def __init__(self, message):
        super().__init__()
        self.description = message

    code = 400
