from flask import make_response


def register_routes(app):
    """

    :param app:

    """

    @app.route("/robots.txt")
    def profile():
        """ """
        return make_response(None, 200)
