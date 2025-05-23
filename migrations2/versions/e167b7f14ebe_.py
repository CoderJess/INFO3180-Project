"""empty message

Revision ID: e167b7f14ebe
Revises: 
Create Date: 2025-05-03 22:26:27.526973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e167b7f14ebe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('favourite',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id_fk', sa.Integer(), nullable=True),
    sa.Column('fav_user_id_fk', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=True),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('password', sa.String(length=200), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('photo', sa.String(length=120), nullable=True),
    sa.Column('date_joined', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id_fk', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('parish', sa.String(length=80), nullable=True),
    sa.Column('biography', sa.String(length=255), nullable=True),
    sa.Column('sex', sa.String(length=20), nullable=True),
    sa.Column('race', sa.String(length=50), nullable=True),
    sa.Column('birth_year', sa.Integer(), nullable=True),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('fav_cuisine', sa.String(length=80), nullable=True),
    sa.Column('fav_colour', sa.String(length=80), nullable=True),
    sa.Column('fav_school_subject', sa.String(length=80), nullable=True),
    sa.Column('political', sa.Boolean(), nullable=True),
    sa.Column('religious', sa.Boolean(), nullable=True),
    sa.Column('family_oriented', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id_fk'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('profile')
    op.drop_table('user')
    op.drop_table('favourite')
    # ### end Alembic commands ###
