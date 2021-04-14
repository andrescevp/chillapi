from chillapi.api import ChillApi

app, api, api_manager, api_config = ChillApi()


if __name__ == '__main__':
    app.run(debug=api_config['app']['debug'], host=api_config['app']['host'], port=api_config['app']['port'])
