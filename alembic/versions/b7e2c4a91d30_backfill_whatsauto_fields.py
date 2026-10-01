"""Backfill nullable configuration fields introduced by the subscription migration."""
from alembic import op

revision = "b7e2c4a91d30"
down_revision = "9f1d2a4c7e11"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("UPDATE users SET subscription_status = 'EXPIRED' WHERE subscription_status IS NULL")
    op.execute("UPDATE bot_configs SET description = '' WHERE description IS NULL")
    op.execute("UPDATE bot_configs SET products = '' WHERE products IS NULL")
    op.execute("UPDATE bot_configs SET instructions = '' WHERE instructions IS NULL")
    op.execute("UPDATE bot_configs SET handover_number = '' WHERE handover_number IS NULL")
    op.execute("UPDATE conversations SET customer_name = '' WHERE customer_name IS NULL")

def downgrade():
    pass
