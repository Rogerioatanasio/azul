from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef7513eabd2b'
down_revision = 'cd7877ac6130'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('trabalhador', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'destaque',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )
        batch_op.add_column(
            sa.Column(
                'plano',
                sa.String(length=20),
                nullable=False,
                server_default='gratis'
            )
        )


def downgrade():
    with op.batch_alter_table('trabalhador', schema=None) as batch_op:
        batch_op.drop_column('plano')
        batch_op.drop_column('destaque')