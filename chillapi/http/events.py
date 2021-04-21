import abc
from typing import List

from chillapi import ApiManager
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


class RequestEvent:
    def on_event(
            self,
            manager: ApiManager,
            resource: AutomaticResource,
            model_name: str,
            table_name: str,
            columns_map: dict,
            table_fields_excluded: List[str],
            id_field: str,
            record_id: any,
            response: dict
            ) -> dict:
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
