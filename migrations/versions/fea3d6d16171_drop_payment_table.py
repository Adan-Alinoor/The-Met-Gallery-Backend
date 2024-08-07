"""Drop payment table

Revision ID: fea3d6d16171
Revises: d578c69d95f6
Create Date: 2024-08-06 21:50:13.017106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fea3d6d16171'
down_revision = 'd578c69d95f6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payments')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payments',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('event_id', sa.INTEGER(), nullable=True),
    sa.Column('ticket_id', sa.INTEGER(), nullable=True),
    sa.Column('transaction_id', sa.VARCHAR(length=255), nullable=False),
    sa.Column('amount', sa.FLOAT(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=50), nullable=True),
    sa.Column('result_desc', sa.VARCHAR(length=255), nullable=True),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], name='fk_payments_event_id_events'),
    sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], name='fk_payments_ticket_id_tickets'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_payments_user_id_users'),
    sa.PrimaryKeyConstraint('id', name='pk_payments'),
    sa.UniqueConstraint('transaction_id', name='uq_payments_transaction_id')
    )
    # ### end Alembic commands ###