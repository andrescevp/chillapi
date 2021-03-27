from flask_restful_swagger_3 import Api
# from swagger_ui import api as api_doc
from api_config import app

from src.application.api_generator import build

api = Api(app, version='0.0', api_spec_url='/api/swagger')

@app.route("/")
def home():
    return {}


# app.app_context().push()

# def create_app():
    # api_doc(app, config_path='/api/swagger.json', url_prefix='/api', title='API doc')

    # api.add_resource(LocationEventsResource, '/api/location_events')
    # build(api, Client, 'Client', 'client', [], {})
    # build(api, ClientLocation, 'ClientLocation', 'client_location', [], {
    #     'client': (lambda: QuerySelectField(query_factory=client_form_chices,
    #                             allow_blank=False))
    # })

    # app.app_context().push()
    # return app

if __name__ == '__main__':
    app.run(debug=True)