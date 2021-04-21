from chillapi.extensions.events import AfterResponseEvent, BeforeRequestEvent, BeforeResponseEvent
from chillapi.swagger import BeforeRequestEventType, BeforeResponseEventType
from chillapi.swagger.http import AutomaticResource


class MyBeforeRequestEvent(BeforeRequestEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeResponseEventType:
        print('MyBeforeRequestEvent')
        return self


class MyBeforeResponseEvent(BeforeResponseEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        print('MyBeforeResponseEvent')
        return self


class MyAfterResponseEvent(AfterResponseEvent):
    def on_event(self, resource: AutomaticResource, **args):
        print('MyAfterResponseEvent', args['response'])
