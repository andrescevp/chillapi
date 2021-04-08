from chillapi.extensions.events import AfterResponseEvent, BeforeRequestEvent, BeforeResponseEvent
from chillapi.swagger import BeforeRequestEventType, BeforeResponseEventType
from chillapi.swagger.http import AutomaticResource, ResourceResponse


class MyBeforeRequestEvent(BeforeRequestEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeResponseEventType:
        return self


class MyBeforeResponseEvent(BeforeResponseEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        _response: ResourceResponse = args['response']
        if resource.db_table['name'] == 'author':
            _response.response['asin'] = f"mod_{_response.response['asin']}"
        print('MyBeforeResponseEvent')
        return self


class MyAfterResponseEvent(AfterResponseEvent):
    def on_event(self, resource: AutomaticResource, **args):
        print('MyAfterResponseEvent', args['response'])
