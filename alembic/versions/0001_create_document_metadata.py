"""
Create document_metadata table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('doc_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table('document_metadata') 