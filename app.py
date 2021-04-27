from chillapi.api import ChillApi

_resources = ChillApi()
app = _resources.app
api_config = _resources.api_config
if __name__ == '__main__':
    app.run(
        debug=api_config['app']['debug'],
        host=api_config['app']['host'],
        port=api_config['app']['port']
    )
