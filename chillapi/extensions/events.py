import abc

from chillapi.swagger import BeforeRequestEventType, BeforeResponseEventType
from chillapi.swagger.http import AutomaticResource, ResourceResponse


class EventDto:
    bag: dict = None

    def __repr__(self):
        return self.__class__.__name__


class BeforeRequestEvent(EventDto):
    @abc.abstractmethod
    def on_event(
            self,
            resource: AutomaticResource,
            **args
            ) -> BeforeRequestEventType:
        pass


class BeforeResponseEvent(EventDto):
    @abc.abstractmethod
    def on_event(
            self,
            resource: AutomaticResource,
            response: ResourceResponse,
            before_request_event: BeforeRequestEvent = None,
            **args
            ) -> BeforeResponseEventType:
        pass


class AfterResponseEvent(EventDto):
    @abc.abstractmethod
    def on_event(
            self,
            response: object
            ) -> None:
        pass


class NullBeforeRequestEvent(BeforeRequestEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        pass


class NullBeforeResponseEvent(BeforeResponseEvent):
    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        pass


class NullAfterResponseEvent(AfterResponseEvent):
    def on_event(self, resource: AutomaticResource, **args):
        pass
