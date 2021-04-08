from flask import request, has_request_context


def get_request_id():
    request_uuid = None

    if has_request_context():
        request_uuid = request.environ.get("HTTP_X_REQUEST_ID")

    return request_uuid


def get_traced_request_uuid():
    request_uuid = None

    if has_request_context():
        request_uuid = request.environ.get("HTTP_X_TRACED_REQUEST_ID")

    return request_uuid
