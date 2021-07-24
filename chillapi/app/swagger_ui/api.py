"""
Api class, an extention to :class:`flask_restplus` that can convert
backend objects into APIs
"""

import inspect

import flask_restplus

from werkzeug.datastructures import FileStorage

from .types import *
from types import MethodType


class SwaggerUI(flask_restplus.Api):
    """
    Base API class that extends :class:`flask_restplus.Api`
    by add functions to generate API directly from an object
    """

    def post(self, f):
        """
        Decorates the `f` function so that it will be registered as
        a POST method responder
        """
        f.is_post = True
        return f

    def get(self, f):
        """
        Decorates the `f` function so that it will be registered as
        a GET method responder
        """
        f.is_get = True
        return f

    def add_restful_api(self, name: str, backend: object, endpoint: str = None):
        """
        Creates a flask_restplus restful api from the
        routines available in given class
        """
        if endpoint is None:
            endpoint = name.replace(" ", "_").lower()
        ns = flask_restplus.Namespace(name, inspect.getdoc(backend), f"/{endpoint}")

        def isempty(o):
            "Checks if an annotation or a default value is empty"
            return o == inspect.Parameter.empty

        def build_resource(callable, post_parser, get_parser, is_post, is_get):
            "Instantiates an ApiMember in closure"

            def invoke_callable(parser, *args, **kwargs):
                for key, value in parser.parse_args().items():
                    kwargs[key] = value
                return callable(*args, **kwargs)

            if is_post:
                if is_get:

                    class ApiMember(flask_restplus.Resource):
                        @ns.expect(post_parser)
                        def post(self, *args, **kwargs):
                            return invoke_callable(post_parser, *args, **kwargs)

                        @ns.expect(get_parser)
                        def get(self, *args, **kwargs):
                            return invoke_callable(get_parser, *args, **kwargs)

                else:

                    class ApiMember(flask_restplus.Resource):
                        @ns.expect(post_parser)
                        def post(self, *args, **kwargs):
                            return invoke_callable(post_parser, *args, **kwargs)

            else:

                class ApiMember(flask_restplus.Resource):
                    @ns.expect(get_parser)
                    def get(self, *args, **kwargs):
                        return invoke_callable(get_parser, *args, **kwargs)

            return ApiMember

        member_resources = {}
        for name, value in inspect.getmembers(backend, inspect.ismethod):
            if name.startswith("_"):
                continue
            is_post = hasattr(value, "is_post") and value.is_post
            is_get = hasattr(value, "is_get") and value.is_get
            if not (is_post or is_get):
                is_post = True
            signature = inspect.signature(value)
            post_parser = ns.parser()
            get_parser = ns.parser()
            for p in signature.parameters.values():
                param_type = str if isempty(p.annotation) else p.annotation
                param_action = "store"
                param_location = {"get": "args", "post": "form"}
                param_choices = ()
                if isinstance(param_type, listof):
                    param_type = param_type.subtype
                    param_action = "append"
                try:
                    if issubclass(param_type, file):
                        is_get = False
                        is_post = True
                        param_type = FileStorage
                        param_location = {"get": "files", "post": "files"}
                except:
                    pass
                if isinstance(param_type, enum):
                    param_choices = tuple(param_type.entries.keys())
                    param_type = str
                post_parser.add_argument(
                    p.name,
                    location=param_location["post"],
                    type=param_type,
                    action=param_action,
                    choices=param_choices,
                    required=isempty(p.default),
                    default=None if isempty(p.default) else p.default,
                )
                get_parser.add_argument(
                    p.name,
                    location=param_location["get"],
                    type=param_type,
                    action=param_action,
                    choices=param_choices,
                    required=isempty(p.default),
                    default=None if isempty(p.default) else p.default,
                )

            resource = build_resource(value, post_parser, get_parser, is_post, is_get)
            member_resources[value] = resource
            ns.route("/" + name)(resource)

        self.add_namespace(ns)

        def backend_url_for(backend, method):
            "Provide the backend with a means to get urls for its methods"
            if method not in backend.member_resources:
                return
            return self.url_for(backend.member_resources[method])

        backend.member_resources = member_resources
        backend.url_for = MethodType(backend_url_for, backend)
