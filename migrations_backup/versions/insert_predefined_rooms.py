"""Insert predefined rooms

Revision ID: insert_predefined_rooms
Revises: 909504bfc3f0
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'insert_predefined_rooms'
down_revision = '909504bfc3f0'
branch_labels = None
depends_on = None

def upgrade():
    # Create a temporary table to store room data
    room_table = sa.table('room',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('created_at', sa.DateTime),
        sa.column('is_private', sa.Boolean),
        sa.column('activity_level', sa.Float),
        sa.column('engagement_rate', sa.Float),
        sa.column('avg_sentiment', sa.Float)
    )

    # List of Indian states
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi"
    ]

    # Product categories
    products = [
        "Credit Cards",
        "Demat Accounts",
        "Loans",
        "Savings Account",
        "Insurance",
        "Line of Credit",
        "Investment"
    ]

    # Generate room data
    room_data = []
    for state in states:
        for product in products:
            room_data.append({
                'name': f"{state} - {product}",
                'description': f"Official chat room for {product} trading in {state}",
                'created_at': datetime.utcnow(),
                'is_private': False,
                'activity_level': 0.0,
                'engagement_rate': 0.0,
                'avg_sentiment': 0.0
            })

    # Insert the rooms
    op.bulk_insert(room_table, room_data)

def downgrade():
    # Delete all predefined rooms
    op.execute('DELETE FROM room') 