from chillapi.api import ChillApi

app, api, api_manager, api_config = ChillApi()

@app.route("/")
def home():
    return {}


# api_manager.create_api(api)

# register_routes_sitemap(app)

# app.app_context().push()

# def create_app():


# api.add_resource(LocationEventsResource, '/api/location_events')
# build(api, Client, 'Client', 'client', [], {})
# build(api, ClientLocation, 'ClientLocation', 'client_location', [], {
#     'client': (lambda: QuerySelectField(query_factory=client_form_chices,
#                             allow_blank=False))
# })

# app.app_context().push()
# return app

if __name__ == '__main__':
    app.run(debug=api_config['app']['debug'], host=api_config['app']['host'], port=api_config['app']['port'])
