"""add vision_board_snapshots and vision_score_snapshots (backlog #21, #22)

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vision_board_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('board_id', sa.String(length=50), nullable=False, server_default='main'),
        sa.Column('label', sa.String(length=200), nullable=True),
        sa.Column('cards_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_vision_board_snapshots_user_id', 'vision_board_snapshots', ['user_id'])

    op.create_table(
        'vision_score_snapshots',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('pillars', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_vision_score_snapshots_user_id', 'vision_score_snapshots', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_vision_score_snapshots_user_id', table_name='vision_score_snapshots')
    op.drop_table('vision_score_snapshots')
    op.drop_index('ix_vision_board_snapshots_user_id', table_name='vision_board_snapshots')
    op.drop_table('vision_board_snapshots')
