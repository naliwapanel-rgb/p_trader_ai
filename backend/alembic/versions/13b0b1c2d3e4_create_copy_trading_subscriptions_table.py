"""create copy trading subscriptions table
Revision ID: 13b0b1c2d3e4
Revises: 13a0b1c2d3e4
Create Date: 2026-07-22
"""
from collections.abc import (
    Sequence,
)
from alembic import (
    op,
)
import sqlalchemy as sa
revision: str = "13b0b1c2d3e4"
down_revision: str | None = (
    "13a0b1c2d3e4"
)
branch_labels: (
    str | Sequence[str] | None
) = None
depends_on: (
    str | Sequence[str] | None
) = None
def upgrade() -> None:
    op.create_table(
        "copy_trading_subscriptions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "follower_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "source_template_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "follower_bot_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "execution_mode",
            sa.String(length=20),
            server_default="PAPER_ONLY",
            nullable=False,
        ),
        sa.Column(
            "subscribed_template_version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "last_mirrored_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('ACTIVE', 'PAUSED', "
                "'STOPPED')"
            ),
            name=(
                "ck_copy_trading_"
                "status"
            ),
        ),
        sa.CheckConstraint(
            (
                "execution_mode = "
                "'PAPER_ONLY'"
            ),
            name=(
                "ck_copy_trading_"
                "paper_only"
            ),
        ),
        sa.CheckConstraint(
            (
                "subscribed_template_version "
                ">= 1"
            ),
            name=(
                "ck_copy_trading_"
                "template_version"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["follower_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_template_id"],
            ["strategy_templates.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["follower_bot_id"],
            ["trading_bots.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id"
        ),
        sa.UniqueConstraint(
            "follower_bot_id",
            name=(
                "uq_copy_trading_"
                "follower_bot"
            ),
        ),
    )
    indexes = [
        (
            "ix_copy_trading_"
            "subscriptions_id",
            ["id"],
        ),
        (
            "ix_copy_trading_"
            "subscriptions_follower_user_id",
            ["follower_user_id"],
        ),
        (
            "ix_copy_trading_"
            "subscriptions_source_template_id",
            ["source_template_id"],
        ),
        (
            "ix_copy_trading_"
            "subscriptions_follower_bot_id",
            ["follower_bot_id"],
        ),
        (
            "ix_copy_trading_"
            "subscriptions_status",
            ["status"],
        ),
        (
            "ix_copy_trading_"
            "subscriptions_updated_at",
            ["updated_at"],
        ),
        (
            "ix_copy_trading_"
            "follower_status",
            [
                "follower_user_id",
                "status",
            ],
        ),
        (
            "ix_copy_trading_"
            "template_status",
            [
                "source_template_id",
                "status",
            ],
        ),
        (
            "ix_copy_trading_"
            "follower_updated",
            [
                "follower_user_id",
                "updated_at",
            ],
        ),
    ]
    for name, columns in indexes:
        op.create_index(
            name,
            "copy_trading_subscriptions",
            columns,
            unique=False,
        )
def downgrade() -> None:
    indexes = [
        (
            "ix_copy_trading_"
            "follower_updated"
        ),
        (
            "ix_copy_trading_"
            "template_status"
        ),
        (
            "ix_copy_trading_"
            "follower_status"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_updated_at"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_status"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_follower_bot_id"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_source_template_id"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_follower_user_id"
        ),
        (
            "ix_copy_trading_"
            "subscriptions_id"
        ),
    ]
    for name in indexes:
        op.drop_index(
            name,
            table_name=(
                "copy_trading_subscriptions"
            ),
        )
    op.drop_table(
        "copy_trading_subscriptions"
    )
