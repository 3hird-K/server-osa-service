"""Remove profiles table

Revision ID: 38fe2984a98c
Revises: 38fe2984a98b
Create Date: 2026-04-07 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38fe2984a98c'
down_revision: Union[str, Sequence[str], None] = '38fe2984a98b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop profiles table."""
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')


def downgrade() -> None:
    """Downgrade schema - recreate profiles table."""
    op.create_table('profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('firstname', sa.String(), nullable=True),
    sa.Column('lastname', sa.String(), nullable=True),
    sa.Column('account_type', sa.String(), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)
