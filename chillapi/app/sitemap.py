import json

from flask import url_for


def register_routes(app):
    """

    :param app:

    """

    def has_no_empty_params(rule):
        """

        :param rule:

        """
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    @app.route("/sitemap")
    def site_map():
        """ """
        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            if has_no_empty_params(rule):
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                links.append((url, rule.endpoint))
        return json.dumps(links)

        # links is now a list of url, endpoint tuples
