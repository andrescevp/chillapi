import pathlib

from chillapi.api import ChillApi
CWD = pathlib.Path(__file__).parent.absolute()

app, api, api_manager, api_config, db, data_repository = ChillApi(config_file=f'{CWD}/../fixtures/api.yaml')

if __name__ == '__main__':
    app.run(
        debug=api_config['app']['debug'],
        host=api_config['app']['host'],
        port=api_config['app']['port']
    )
