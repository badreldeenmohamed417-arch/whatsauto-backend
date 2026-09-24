"""Add WhatsAuto subscription, business fields and customer names."""
from alembic import op
import sqlalchemy as sa

revision = "9f1d2a4c7e11"
down_revision = "46330379a1ff"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("subscription_status", sa.String(), nullable=True, server_default="EXPIRED"))
    op.add_column("users", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bot_configs", sa.Column("description", sa.Text(), nullable=True, server_default=""))
    op.add_column("bot_configs", sa.Column("products", sa.Text(), nullable=True, server_default=""))
    op.add_column("bot_configs", sa.Column("instructions", sa.Text(), nullable=True, server_default=""))
    op.add_column("bot_configs", sa.Column("handover_number", sa.String(), nullable=True, server_default=""))
    op.add_column("conversations", sa.Column("customer_name", sa.String(), nullable=True, server_default=""))

def downgrade():
    op.drop_column("conversations", "customer_name")
    op.drop_column("bot_configs", "handover_number")
    op.drop_column("bot_configs", "instructions")
    op.drop_column("bot_configs", "products")
    op.drop_column("bot_configs", "description")
    op.drop_column("users", "expires_at")
    op.drop_column("users", "subscription_status")
