from flask import make_response


def register_routes(app):
    @app.route("/robots.txt")
    def profile():
        return make_response(None, 200)
