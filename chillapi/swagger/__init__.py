from typing import TypeVar

BeforeRequestEventType = TypeVar("BeforeRequestEventType", bound="BeforeRequestEvent")  # noqa F821
BeforeResponseEventType = TypeVar("BeforeResponseEventType", bound="BeforeResponseEvent")  # noqa F821
AfterResponseEventType = TypeVar("AfterResponseEventType", bound="AfterResponseEvent")  # noqa F821
