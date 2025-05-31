"""add sales intent column

Revision ID: add_sales_intent
Revises: 69062d5c9085
Create Date: 2024-03-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sales_intent'
down_revision = '69062d5c9085'
branch_labels = None
depends_on = None


def upgrade():
    # Add sales_intent column to message table
    op.add_column('message', sa.Column('sales_intent', sa.String(20), nullable=True, server_default='exploring'))


def downgrade():
    # Remove sales_intent column from message table
    op.drop_column('message', 'sales_intent') 