from abc import ABC, abstractmethod

from scripts.providers.contracts import ConversationRequest, ConversationResponse


class BaseProvider(ABC):
    """Common provider interface for native and compatible adapters."""

    @abstractmethod
    def chat(self, request: ConversationRequest) -> ConversationResponse:
        raise NotImplementedError
