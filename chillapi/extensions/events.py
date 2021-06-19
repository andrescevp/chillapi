import abc

from chillapi.swagger import BeforeRequestEventType, BeforeResponseEventType
from chillapi.swagger.http import AutomaticResource, ResourceResponse


class EventDto:
    """ """

    bag: dict = None

    def __repr__(self):
        return self.__class__.__name__

    def for_json(self):
        """ """
        return {"name": self.__class__.__name__}


class BeforeRequestEvent(EventDto):
    """ """

    @abc.abstractmethod
    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        """

        :param resource: AutomaticResource:
        :param **args:

        """
        pass


class BeforeResponseEvent(EventDto):
    """ """

    @abc.abstractmethod
    def on_event(
        self, resource: AutomaticResource, response: ResourceResponse, before_request_event: BeforeRequestEvent = None, **args
    ) -> BeforeResponseEventType:
        """

        :param resource: AutomaticResource:
        :param response: ResourceResponse:
        :param before_request_event: BeforeRequestEvent:  (Default value = None)
        :param **args:

        """
        pass


class AfterResponseEvent(EventDto):
    """ """

    @abc.abstractmethod
    def on_event(self, response: object) -> None:
        """

        :param response: object:

        """
        pass


class NullBeforeRequestEvent(BeforeRequestEvent):
    """ """

    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        """

        :param resource: AutomaticResource:
        :param **args:

        """
        pass


class NullBeforeResponseEvent(BeforeResponseEvent):
    """ """

    def on_event(self, resource: AutomaticResource, **args) -> BeforeRequestEventType:
        """

        :param resource: AutomaticResource:
        :param **args:

        """
        pass


class NullAfterResponseEvent(AfterResponseEvent):
    """ """

    def on_event(self, resource: AutomaticResource, **args):
        """

        :param resource: AutomaticResource:
        :param **args:

        """
        pass
