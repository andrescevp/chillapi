"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    # conn = op.get_bind()
    # conn.execute(
    #         text(
    #             """
    #             -- @TODO fill sql statement
    #             """
    #         )
    #     )
    ${upgrades if upgrades else "pass"}


def downgrade():
    # conn = op.get_bind()
    # conn.execute(
    #         text(
    #             """
    #             -- @TODO fill rollback sql statement
    #             """
    #         )
    #     )
    ${downgrades if downgrades else "pass"}
