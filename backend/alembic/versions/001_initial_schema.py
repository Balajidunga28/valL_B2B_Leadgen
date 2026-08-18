"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Companies
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(255), nullable=True),
        sa.Column('categories', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('city', sa.String(255), nullable=True),
        sa.Column('state', sa.String(255), nullable=True),
        sa.Column('country', sa.String(100), nullable=True, server_default='India'),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('phone_intl', sa.String(50), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('rating', sa.Numeric(2, 1), nullable=True),
        sa.Column('review_count', sa.Integer, nullable=True),
        sa.Column('business_status', sa.String(50), nullable=True),
        sa.Column('google_maps_url', sa.String(500), nullable=True),
        sa.Column('source_place_id', sa.String(255), nullable=True),
        sa.Column('source_cin', sa.String(20), nullable=True),
        sa.Column('completeness_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_companies_org_domain', 'companies', ['organization_id', 'domain'])
    op.create_index('ix_companies_org_place_id', 'companies', ['organization_id', 'source_place_id'])
    op.create_index('ix_companies_org_cin', 'companies', ['organization_id', 'source_cin'])
    op.create_index('ix_companies_org_name', 'companies', ['organization_id', 'name'])
    op.create_index('ix_companies_city_state', 'companies', ['city', 'state'])

    # Pipeline Runs
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('query_params', postgresql.JSONB, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('sources_used', postgresql.ARRAY(sa.Text), nullable=False, server_default='{}'),
        sa.Column('total_extracted', sa.Integer, nullable=True),
        sa.Column('total_cleaned', sa.Integer, nullable=True),
        sa.Column('total_deduplicated', sa.Integer, nullable=True),
        sa.Column('total_valid', sa.Integer, nullable=True),
        sa.Column('total_enriched', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Raw Records
    op.create_table(
        'raw_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_runs.id'), nullable=False, index=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True, index=True),
        sa.Column('source_adapter', sa.String(100), nullable=False),
        sa.Column('source_record_id', sa.String(255), nullable=True),
        sa.Column('raw_data', postgresql.JSONB, nullable=False),
        sa.Column('normalized_data', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='extracted'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_raw_records_org_pipeline', 'raw_records', ['organization_id', 'pipeline_run_id'])
    op.create_index('ix_raw_records_org_source', 'raw_records', ['organization_id', 'source_adapter'])

    # Leads
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False, index=True),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_runs.id'), nullable=False, index=True),
        sa.Column('raw_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('raw_records.id'), nullable=False),
        sa.Column('validation_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('validation_issues', postgresql.JSONB, nullable=True),
        sa.Column('enrichment_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('lead_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('score_version', sa.String(50), nullable=True),
        sa.Column('score_components', postgresql.JSONB, nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Source API Keys
    op.create_table(
        'source_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('source_adapter', sa.String(100), nullable=False),
        sa.Column('api_key_encrypted', sa.Text, nullable=False),
        sa.Column('api_key_hint', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quota_used', sa.Integer, nullable=True, server_default='0'),
        sa.Column('quota_limit', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('source_api_keys')
    op.drop_table('leads')
    op.drop_table('raw_records')
    op.drop_table('pipeline_runs')
    op.drop_table('companies')
    op.drop_table('users')
    op.drop_table('organizations')
