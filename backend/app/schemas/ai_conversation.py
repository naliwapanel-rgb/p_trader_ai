from datetime import datetime
from typing import (
    Any,
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)
AIConversationStatus = Literal[
    "ACTIVE",
    "ARCHIVED",
]
AIMessageRole = Literal[
    "USER",
    "ASSISTANT",
    "SYSTEM",
]
AIStoredAnalysisType = Literal[
    "GENERAL",
    "MARKET",
    "PORTFOLIO",
    "RISK",
    "TRADE_PLAN",
    "ARBITRAGE",
]
class AIConversationCreateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    @field_validator("title")
    @classmethod
    def normalize_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "title cannot be blank"
            )
        return normalized
class AIConversationUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    status: (
        AIConversationStatus | None
    ) = None
    @field_validator("title")
    @classmethod
    def normalize_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "title cannot be blank"
            )
        return normalized
    @model_validator(mode="after")
    def require_update_value(self):
        if not self.model_fields_set:
            raise ValueError(
                "At least one conversation "
                "field must be provided"
            )
        return self
class AIConversationExchangeCreate(BaseModel):
    user_content: str = Field(
        min_length=2,
        max_length=20000,
    )
    assistant_content: str = Field(
        min_length=2,
        max_length=50000,
    )
    analysis_type: (
        AIStoredAnalysisType
    ) = "GENERAL"
    user_metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
    assistant_metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
    @field_validator(
        "user_content",
        "assistant_content",
    )
    @classmethod
    def normalize_content(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "message content cannot "
                "be blank"
            )
        return normalized
class AIConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: AIConversationStatus
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True,
    }
class AIMessageResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    role: AIMessageRole
    content: str
    analysis_type: (
        AIStoredAnalysisType | None
    )
    message_metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )
    created_at: datetime
    model_config = {
        "from_attributes": True,
    }
class AIConversationSummaryResponse(
    AIConversationResponse
):
    message_count: int = Field(
        ge=0,
    )
    last_message_at: (
        datetime | None
    ) = None
class AIConversationHistoryResponse(
    BaseModel
):
    conversation: (
        AIConversationSummaryResponse
    )
    messages: list[
        AIMessageResponse
    ] = Field(
        default_factory=list
    )
class AIConversationExchangeResponse(
    BaseModel
):
    conversation: (
        AIConversationSummaryResponse
    )
    user_message: AIMessageResponse
    assistant_message: AIMessageResponse
