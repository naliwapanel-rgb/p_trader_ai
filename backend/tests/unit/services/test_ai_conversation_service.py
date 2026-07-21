from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    Mock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.ai_conversation import (
    AIConversationCreateRequest,
    AIConversationExchangeCreate,
    AIConversationUpdateRequest,
)
from app.services.ai_conversation_service import (
    AIConversationService,
)
def _now():
    return datetime.now(UTC)
def _conversation(
    *,
    conversation_id=10,
    user_id=7,
    title="New conversation",
    status="ACTIVE",
):
    return SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title=title,
        status=status,
        created_at=_now(),
        updated_at=_now(),
    )
def _message(
    *,
    message_id,
    role,
    content,
):
    return SimpleNamespace(
        id=message_id,
        conversation_id=10,
        user_id=7,
        role=role,
        content=content,
        analysis_type="GENERAL",
        message_metadata={},
        created_at=_now(),
    )
def _service():
    repository = Mock()
    repository.count_messages.return_value = 0
    repository.get_last_message.return_value = None
    return (
        AIConversationService(
            None,
            repository=repository,
        ),
        repository,
    )
def test_create_conversation_uses_user_id():
    service, repository = _service()
    repository.create_conversation.return_value = (
        _conversation()
    )
    result = (
        service.create_conversation(
            current_user=(
                SimpleNamespace(id=7)
            ),
            data=(
                AIConversationCreateRequest()
            ),
        )
    )
    repository.create_conversation.assert_called_once_with(
        user_id=7,
        title="New conversation",
    )
    assert result.user_id == 7
    assert result.message_count == 0
def test_missing_conversation_is_rejected():
    service, repository = _service()
    repository.get_by_id_and_user.return_value = (
        None
    )
    with pytest.raises(
        HTTPException,
        match="AI conversation not found",
    ) as exc_info:
        service.get_history(
            current_user=(
                SimpleNamespace(id=7)
            ),
            conversation_id=99,
        )
    assert (
        exc_info.value.status_code
        == 404
    )
def test_list_returns_user_scoped_summaries():
    service, repository = _service()
    conversation = _conversation(
        title="History"
    )
    repository.list_by_user.return_value = [
        conversation,
    ]
    repository.count_messages.return_value = 2
    repository.get_last_message.return_value = (
        _message(
            message_id=2,
            role="ASSISTANT",
            content="Answer",
        )
    )
    result = service.list_conversations(
        current_user=(
            SimpleNamespace(id=7)
        ),
        limit=25,
        offset=5,
    )
    repository.list_by_user.assert_called_once_with(
        user_id=7,
        limit=25,
        offset=5,
    )
    assert len(result) == 1
    assert result[0].message_count == 2
    assert (
        result[0].last_message_at
        is not None
    )
def test_history_serializes_ordered_messages():
    service, repository = _service()
    conversation = _conversation()
    repository.get_by_id_and_user.return_value = (
        conversation
    )
    repository.list_messages.return_value = [
        _message(
            message_id=1,
            role="USER",
            content="Question",
        ),
        _message(
            message_id=2,
            role="ASSISTANT",
            content="Answer",
        ),
    ]
    repository.count_messages.return_value = 2
    repository.get_last_message.return_value = (
        repository
        .list_messages
        .return_value[1]
    )
    result = service.get_history(
        current_user=(
            SimpleNamespace(id=7)
        ),
        conversation_id=10,
    )
    assert [
        message.role
        for message in result.messages
    ] == [
        "USER",
        "ASSISTANT",
    ]
def test_append_exchange_generates_title():
    service, repository = _service()
    conversation = _conversation()
    repository.get_by_id_and_user.return_value = (
        conversation
    )
    user_message = _message(
        message_id=1,
        role="USER",
        content=(
            "Please review my portfolio"
        ),
    )
    assistant_message = _message(
        message_id=2,
        role="ASSISTANT",
        content="Portfolio reviewed.",
    )
    repository.append_exchange.return_value = (
        user_message,
        assistant_message,
    )
    repository.count_messages.return_value = 2
    repository.get_last_message.return_value = (
        assistant_message
    )
    result = service.append_exchange(
        current_user=(
            SimpleNamespace(id=7)
        ),
        conversation_id=10,
        data=AIConversationExchangeCreate(
            user_content=(
                "Please review my portfolio"
            ),
            assistant_content=(
                "Portfolio reviewed."
            ),
        ),
    )
    call = (
        repository
        .append_exchange
        .call_args
        .kwargs
    )
    assert (
        call["generated_title"]
        == "Please review my portfolio"
    )
    assert (
        call["user_id"]
        == 7
    )
    assert (
        result.user_message.role
        == "USER"
    )
    assert (
        result.assistant_message.role
        == "ASSISTANT"
    )
def test_archived_update_and_delete_rules():
    service, repository = _service()
    archived = _conversation(
        status="ARCHIVED"
    )
    repository.get_by_id_and_user.return_value = (
        archived
    )
    with pytest.raises(
        HTTPException,
        match="AI conversation is archived",
    ) as exc_info:
        service.append_exchange(
            current_user=(
                SimpleNamespace(id=7)
            ),
            conversation_id=10,
            data=AIConversationExchangeCreate(
                user_content="Question",
                assistant_content="Answer",
            ),
        )
    assert (
        exc_info.value.status_code
        == 409
    )
    active = _conversation(
        title="Old title"
    )
    repository.get_by_id_and_user.return_value = (
        active
    )
    repository.update_conversation.return_value = (
        _conversation(
            title="Updated title"
        )
    )
    updated = service.update_conversation(
        current_user=(
            SimpleNamespace(id=7)
        ),
        conversation_id=10,
        data=AIConversationUpdateRequest(
            title="Updated title"
        ),
    )
    assert (
        updated.title
        == "Updated title"
    )
    service.delete_conversation(
        current_user=(
            SimpleNamespace(id=7)
        ),
        conversation_id=10,
    )
    repository.delete_conversation.assert_called_once_with(
        active
    )
