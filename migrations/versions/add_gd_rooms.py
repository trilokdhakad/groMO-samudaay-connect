"""add GD rooms for each state

Revision ID: add_gd_rooms
Revises: fa33581afddf
Create Date: 2024-03-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.chat.routes import INDIAN_STATES
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_gd_rooms'
down_revision = 'fa33581afddf'
branch_labels = None
depends_on = None

def upgrade():
    # Get connection
    conn = op.get_bind()
    
    # Add Others[GD] room for each state
    for state in INDIAN_STATES:
        room_name = f"{state} - Others[GD]"
        description = f"General Discussion room for {state}"
        
        # Insert room
        conn.execute(
            text("""
            INSERT INTO room (name, description, created_at)
            VALUES (:name, :description, CURRENT_TIMESTAMP)
            """),
            {"name": room_name, "description": description}
        )

def downgrade():
    # Get connection
    conn = op.get_bind()
    
    # Remove all Others[GD] rooms
    conn.execute(
        text("""
        DELETE FROM room 
        WHERE name LIKE '% - Others[GD]'
        """)
    ) 