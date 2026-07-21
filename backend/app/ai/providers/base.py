from abc import (
    ABC,
    abstractmethod,
)
from app.schemas.ai_provider import (
    AIProviderRequest,
    AIProviderResponse,
)
class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError
    @property
    @abstractmethod
    def model_name(self) -> str | None:
        raise NotImplementedError
    @abstractmethod
    async def generate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        raise NotImplementedError
