def auth(security_schemes, security, request_obj, endpoint, method):
    # print(request_obj, endpoint, method, security_schemes, security)

    # if strict this can whitelist endpoints
    # if method == 'get' and endpoint == '/read/books':
    #     return True

    # return False
    if not request_obj.headers.get('Authorization'):
        return False
    bearer_token = request_obj.headers.get('Authorization').lstrip('Bearer').strip()
    return bearer_token == 'aaa'
