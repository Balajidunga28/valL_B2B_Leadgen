/**
 * url: /frontend/src/types/index.ts
 * About:
 *   TypeScript type definitions for ValLG frontend. Matches the backend
 *   API response schemas. All types are derived from the Phase 3 data model.
 */

// Auth types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  organization_id: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// Company types
export interface Company {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  categories: string[] | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  phone: string | null;
  phone_intl: string | null;
  website: string | null;
  rating: number | null;
  review_count: number | null;
  business_status: string | null;
  google_maps_url: string | null;
  source_place_id: string | null;
  source_cin: string | null;
  completeness_score: number | null;
  created_at: string;
  updated_at: string;
}

// Lead types (unified from /api/leads)
export interface Lead {
  id: string;
  name: string;
  industry: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  phone: string | null;
  website: string | null;
  rating: number | null;
  review_count: number | null;
  latitude: number | null;
  longitude: number | null;
  source: string | null;
  sources: string[];
  validation_status: string | null;
  enrichment_description: string | null;
  enrichment_email: string | null;
  enrichment_social_links: Record<string, string> | null;
  total_score: number | null;
  score_version: string | null;
  scored_at: string | null;
  is_saved: boolean;
}

// Pipeline run types
export interface PipelineRun {
  id: string;
  name: string | null;
  query_text: string;
  query_params: SearchParams;
  status: string;
  sources_used: string[];
  total_extracted: number | null;
  total_cleaned: number | null;
  total_deduplicated: number | null;
  total_valid: number | null;
  total_enriched: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// Search types
export interface SearchParams {
  query: string;
  country?: string;
  state?: string;
  city?: string;
  industry?: string;
  sources: string[];
  mode: 'keyword' | 'nearby' | 'mca';
  min_rating?: number;
  open_now?: boolean;
  radius?: number;
}

// Pagination types
export interface PaginationMeta {
  page: number;
  per_page: number;
  total_count: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

// Dashboard types
export interface DashboardMetrics {
  total_leads: number;
  valid_leads: number;
  high_score_leads: number;
  exported_leads: number;
}

export interface PipelineActivity {
  stage: string;
  count: number;
}

export interface RecentLead {
  id: string;
  company_name: string;
  created_at: string;
}

// API Error types
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string }>;
  };
}

// API Key types
export interface SourceApiKey {
  id: string;
  source_adapter: string;
  api_key_hint: string;
  status: string;
  last_verified_at: string | null;
  quota_used: number | null;
  quota_limit: number | null;
  created_at: string;
}

// Export types
export interface ExportRecord {
  id: string;
  name: string | null;
  format: string;
  field_list: string[];
  status: string;
  file_size: number | null;
  record_count: number;
  created_at: string;
  completed_at: string | null;
}
