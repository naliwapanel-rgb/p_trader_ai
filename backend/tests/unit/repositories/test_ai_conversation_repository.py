from sqlalchemy import (
    create_engine,
    inspect,
)
from sqlalchemy.orm import (
    sessionmaker,
)
from sqlalchemy.pool import (
    StaticPool,
)
from app.database.session import Base
from app.models import (
    AIConversation,
    AIMessage,
    User,
)
from app.repositories.ai_conversation_repository import (
    AIConversationRepository,
)
def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine
    )
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    return (
        engine,
        session_factory(),
    )
def _create_user(
    db,
    *,
    user_id,
    email,
):
    user = User(
        id=user_id,
        full_name=f"User {user_id}",
        email=email,
        hashed_password="hashed",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user
def test_ai_models_are_registered():
    engine, db = _session()
    try:
        inspector = inspect(engine)
        assert inspector.has_table(
            "ai_conversations"
        )
        assert inspector.has_table(
            "ai_messages"
        )
        assert (
            AIConversation.__tablename__
            == "ai_conversations"
        )
        assert (
            AIMessage.__tablename__
            == "ai_messages"
        )
    finally:
        db.close()
        engine.dispose()
def test_create_and_list_are_user_scoped():
    engine, db = _session()
    try:
        _create_user(
            db,
            user_id=1,
            email="one@example.com",
        )
        _create_user(
            db,
            user_id=2,
            email="two@example.com",
        )
        repository = (
            AIConversationRepository(db)
        )
        first = (
            repository
            .create_conversation(
                user_id=1,
                title="First",
            )
        )
        repository.create_conversation(
            user_id=2,
            title="Other user",
        )
        user_one = (
            repository.list_by_user(
                user_id=1
            )
        )
        assert len(user_one) == 1
        assert user_one[0].id == first.id
        assert (
            repository
            .get_by_id_and_user(
                conversation_id=first.id,
                user_id=2,
            )
            is None
        )
    finally:
        db.close()
        engine.dispose()
def test_append_exchange_is_ordered():
    engine, db = _session()
    try:
        _create_user(
            db,
            user_id=1,
            email="one@example.com",
        )
        repository = (
            AIConversationRepository(db)
        )
        conversation = (
            repository
            .create_conversation(
                user_id=1,
                title="New conversation",
            )
        )
        user_message, assistant = (
            repository.append_exchange(
                conversation=conversation,
                user_id=1,
                user_content="Analyze BTC.",
                assistant_content=(
                    "BTC analysis completed."
                ),
                analysis_type="MARKET",
                user_metadata={
                    "symbols": ["BTCUSDT"],
                },
                assistant_metadata={
                    "execution_allowed": False,
                },
                generated_title=(
                    "Analyze BTC."
                ),
            )
        )
        messages = (
            repository.list_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=1,
            )
        )
        assert messages == [
            user_message,
            assistant,
        ]
        assert messages[0].role == "USER"
        assert (
            messages[1].role
            == "ASSISTANT"
        )
        assert (
            messages[1]
            .message_metadata
            ["execution_allowed"]
            is False
        )
        assert (
            conversation.title
            == "Analyze BTC."
        )
    finally:
        db.close()
        engine.dispose()
def test_message_history_is_user_scoped():
    engine, db = _session()
    try:
        _create_user(
            db,
            user_id=1,
            email="one@example.com",
        )
        _create_user(
            db,
            user_id=2,
            email="two@example.com",
        )
        repository = (
            AIConversationRepository(db)
        )
        conversation = (
            repository
            .create_conversation(
                user_id=1,
                title="Private",
            )
        )
        repository.append_exchange(
            conversation=conversation,
            user_id=1,
            user_content="Private question",
            assistant_content=(
                "Private response"
            ),
            analysis_type="GENERAL",
            user_metadata={},
            assistant_metadata={},
        )
        assert (
            repository.list_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=2,
            )
            == []
        )
        assert (
            repository.count_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=2,
            )
            == 0
        )
    finally:
        db.close()
        engine.dispose()
def test_summary_helpers_return_last_message():
    engine, db = _session()
    try:
        _create_user(
            db,
            user_id=1,
            email="one@example.com",
        )
        repository = (
            AIConversationRepository(db)
        )
        conversation = (
            repository
            .create_conversation(
                user_id=1,
                title="Summary",
            )
        )
        repository.append_exchange(
            conversation=conversation,
            user_id=1,
            user_content="Question",
            assistant_content="Answer",
            analysis_type="GENERAL",
            user_metadata={},
            assistant_metadata={},
        )
        assert (
            repository.count_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=1,
            )
            == 2
        )
        last_message = (
            repository.get_last_message(
                conversation_id=(
                    conversation.id
                ),
                user_id=1,
            )
        )
        assert last_message is not None
        assert (
            last_message.role
            == "ASSISTANT"
        )
    finally:
        db.close()
        engine.dispose()
def test_delete_removes_conversation_messages():
    engine, db = _session()
    try:
        _create_user(
            db,
            user_id=1,
            email="one@example.com",
        )
        repository = (
            AIConversationRepository(db)
        )
        conversation = (
            repository
            .create_conversation(
                user_id=1,
                title="Delete me",
            )
        )
        repository.append_exchange(
            conversation=conversation,
            user_id=1,
            user_content="Question",
            assistant_content="Answer",
            analysis_type="GENERAL",
            user_metadata={},
            assistant_metadata={},
        )
        conversation_id = (
            conversation.id
        )
        repository.delete_conversation(
            conversation
        )
        assert (
            db.query(AIConversation)
            .filter(
                AIConversation.id
                == conversation_id
            )
            .count()
            == 0
        )
        assert (
            db.query(AIMessage)
            .filter(
                AIMessage.conversation_id
                == conversation_id
            )
            .count()
            == 0
        )
    finally:
        db.close()
        engine.dispose()
