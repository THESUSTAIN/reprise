"""add vision_cards unified model (backlog #1)

Cree la table vision_cards : modele unifie du canvas Vision Board (remplace
le double systeme CanvasElement JSON blob + live cards codees en dur).
Voir models.py::VisionCard et routes/vision_cards.py pour le detail.

Revision ID: a1b2c3d4e5f6
Revises: d1f37630ccad
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd1f37630ccad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'vision_cards',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('board_id', sa.String(length=50), nullable=False, server_default='main'),
        sa.Column('card_type', sa.String(length=30), nullable=False, server_default='postit'),
        sa.Column('entity_type', sa.String(length=30), nullable=True),
        sa.Column('entity_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=True),
        sa.Column('manual_content', sa.Text(), nullable=True),
        sa.Column('x', sa.Float(), nullable=False, server_default='40'),
        sa.Column('y', sa.Float(), nullable=False, server_default='40'),
        sa.Column('width', sa.Float(), nullable=False, server_default='220'),
        sa.Column('height', sa.Float(), nullable=False, server_default='140'),
        sa.Column('rotation', sa.Float(), nullable=False, server_default='0'),
        sa.Column('z', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('style', sa.JSON(), nullable=True),
        sa.Column('connections', sa.JSON(), nullable=True),
        sa.Column('cache_label', sa.String(length=300), nullable=True),
        sa.Column('cache_value', sa.String(length=300), nullable=True),
        sa.Column('cache_progress', sa.Float(), nullable=True),
        sa.Column('cache_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_vision_cards_user_id', 'vision_cards', ['user_id'])
    op.create_index('ix_vision_cards_board_id', 'vision_cards', ['board_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_vision_cards_board_id', table_name='vision_cards')
    op.drop_index('ix_vision_cards_user_id', table_name='vision_cards')
    op.drop_table('vision_cards')
