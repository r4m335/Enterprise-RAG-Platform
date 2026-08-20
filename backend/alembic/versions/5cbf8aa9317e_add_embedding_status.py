"""add embedding status

Revision ID: 5cbf8aa9317e
Revises: a2980a297243
Create Date: 2026-08-20 17:03:15.218431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5cbf8aa9317e'
down_revision: Union[str, Sequence[str], None] = 'a2980a297243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('documents', 'status', new_column_name='processing_status')
    
    embedding_status_enum = postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='embeddingstatus')
    embedding_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('documents', sa.Column('embedding_status', embedding_status_enum, nullable=False, server_default='PENDING'))
    op.add_column('documents', sa.Column('embedding_error', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'embedding_error')
    op.drop_column('documents', 'embedding_status')
    
    op.alter_column('documents', 'processing_status', new_column_name='status')
    
    embedding_status_enum = postgresql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='embeddingstatus')
    embedding_status_enum.drop(op.get_bind(), checkfirst=True)
