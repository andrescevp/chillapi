import pathlib

from chillapi.api import ChillApi

CWD = pathlib.Path(__file__).parent.absolute()

_resources = ChillApi(config_file = f'{CWD}/../fixtures/api.yaml')
app = _resources.app
db = _resources.db
_api_config = _resources.api_config
if __name__ == '__main__':
    app.run(
            debug = _api_config['app']['debug'],
            host = _api_config['app']['host'],
            port = _api_config['app']['port']
            )
