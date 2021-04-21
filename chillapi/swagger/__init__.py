from typing import TypeVar

BeforeRequestEventType = TypeVar('BeforeRequestEventType', bound = 'BeforeRequestEvent')
BeforeResponseEventType = TypeVar('BeforeResponseEventType', bound = 'BeforeResponseEvent')
AfterResponseEventType = TypeVar('AfterResponseEventType', bound = 'AfterResponseEvent')
