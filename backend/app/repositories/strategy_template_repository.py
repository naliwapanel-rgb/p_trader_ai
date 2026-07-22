from datetime import (
    UTC,
    datetime,
)
from typing import (
    Any,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.strategy_template import (
    StrategyTemplate,
)
class StrategyTemplateRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
    def create(
        self,
        *,
        user_id: int,
        fields: dict[str, Any],
    ) -> StrategyTemplate:
        template = StrategyTemplate(
            user_id=user_id,
            **dict(fields),
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    def get_by_id_and_user(
        self,
        *,
        template_id: int,
        user_id: int,
    ) -> StrategyTemplate | None:
        return (
            self.db.query(
                StrategyTemplate
            )
            .filter(
                StrategyTemplate.id
                == template_id,
                StrategyTemplate.user_id
                == user_id,
            )
            .first()
        )
    def get_by_name_and_user(
        self,
        *,
        name: str,
        user_id: int,
    ) -> StrategyTemplate | None:
        return (
            self.db.query(
                StrategyTemplate
            )
            .filter(
                StrategyTemplate.name
                == name,
                StrategyTemplate.user_id
                == user_id,
            )
            .first()
        )

    def get_published_by_id(
        self,
        *,
        template_id: int,
    ) -> StrategyTemplate | None:
        return (
            self.db.query(
                StrategyTemplate
            )
            .filter(
                StrategyTemplate.id
                == template_id,
                StrategyTemplate.visibility
                == "PUBLIC",
                StrategyTemplate.status
                == "PUBLISHED",
            )
            .first()
        )
    def list_by_user(
        self,
        *,
        user_id: int,
        status: str | None = None,
        visibility: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StrategyTemplate]:
        query = (
            self.db.query(
                StrategyTemplate
            )
            .filter(
                StrategyTemplate.user_id
                == user_id
            )
        )
        if status is not None:
            query = query.filter(
                StrategyTemplate.status
                == status
            )
        if visibility is not None:
            query = query.filter(
                StrategyTemplate.visibility
                == visibility
            )
        return (
            query.order_by(
                StrategyTemplate
                .updated_at
                .desc(),
                StrategyTemplate.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def list_published(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StrategyTemplate]:
        return (
            self.db.query(
                StrategyTemplate
            )
            .filter(
                StrategyTemplate.visibility
                == "PUBLIC",
                StrategyTemplate.status
                == "PUBLISHED",
            )
            .order_by(
                StrategyTemplate
                .updated_at
                .desc(),
                StrategyTemplate.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def update_fields(
        self,
        *,
        template: StrategyTemplate,
        fields: dict[str, Any],
    ) -> StrategyTemplate:
        protected_fields = {
            "id",
            "user_id",
            "created_at",
        }
        prohibited = (
            protected_fields
            .intersection(fields)
        )
        if prohibited:
            names = ", ".join(
                sorted(prohibited)
            )
            raise ValueError(
                "Protected strategy template "
                f"fields cannot be updated: "
                f"{names}"
            )
        for key, value in fields.items():
            setattr(
                template,
                key,
                value,
            )
        template.updated_at = (
            datetime.now(UTC)
        )
        self.db.commit()
        self.db.refresh(template)
        return template
    def delete(
        self,
        template: StrategyTemplate,
    ) -> None:
        self.db.delete(template)
        self.db.commit()
