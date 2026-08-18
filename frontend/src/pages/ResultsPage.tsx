/**
 * url: /frontend/src/pages/ResultsPage.tsx
 * About:
 *   Results page for ValLG. Shows all scored/enriched leads from the
 *   unified /api/leads endpoint with server-side filtering. Displays
 *   company name, industry, location, phone, website, rating, source,
 *   lead score, and validation status.
 */

import { useEffect, useState, useMemo, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, Button, PageHeader, EmptyState, Skeleton } from '../components/ui';
import type { Lead } from '../types';

const SOURCE_MAP: Record<string, { label: string; color: string }> = {
  google_search: { label: 'Google Maps', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
  google_places: { label: 'Google Places', color: 'bg-green-500/20 text-green-300 border-green-500/30' },
  openstreetmap: { label: 'OpenStreetMap', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' },
  web_search: { label: 'Web Search', color: 'bg-orange-500/20 text-orange-300 border-orange-500/30' },
  indiamart: { label: 'IndiaMART', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
  justdial: { label: 'JustDial', color: 'bg-pink-500/20 text-pink-300 border-pink-500/30' },
  aggregated: { label: 'Aggregated', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
};

function SourceBadge({ source }: { source: string | null }) {
  if (!source) return <span className="text-dark-400">—</span>;
  const info = SOURCE_MAP[source] || { label: source, color: 'bg-dark-600 text-dark-200 border-dark-500' };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${info.color}`}>
      {info.label}
    </span>
  );
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return <span className="text-dark-400">—</span>;
  let color = 'text-dark-300';
  if (score >= 60) color = 'text-emerald-400';
  else if (score >= 35) color = 'text-amber-400';
  else color = 'text-red-400';
  return <span className={`font-mono font-semibold ${color}`}>{score.toFixed(1)}</span>;
}

function ValidationBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-dark-400">—</span>;
  const colors: Record<string, string> = {
    VALID: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    INVALID: 'bg-red-500/20 text-red-300 border-red-500/30',
    UNKNOWN: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${colors[status] || 'bg-dark-600 text-dark-200 border-dark-500'}`}>
      {status}
    </span>
  );
}

export default function ResultsPage() {
  const location = useLocation();
  const searchId = (location.state as { searchId?: string; query?: string })?.searchId || null;
  const searchQuery = (location.state as { searchId?: string; query?: string })?.query || null;
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Server-side filters
  const [filterMinScore, setFilterMinScore] = useState('');
  const [filterMaxScore, setFilterMaxScore] = useState('');
  const [filterIndustry, setFilterIndustry] = useState('');
  const [filterCity, setFilterCity] = useState('');
  const [filterHasPhone, setFilterHasPhone] = useState<boolean | null>(null);
  const [filterHasEmail, setFilterHasEmail] = useState<boolean | null>(null);
  const [filterValidation, setFilterValidation] = useState('');

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const allLeads: Lead[] = [];
      let offset = 0;
      const limit = 200;
      let hasMore = true;

      while (hasMore) {
        const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
        if (searchId) params.set('search_id', searchId);
        if (filterMinScore) params.set('min_score', filterMinScore);
        if (filterMaxScore) params.set('max_score', filterMaxScore);
        if (filterIndustry) params.set('industry', filterIndustry);
        if (filterCity) params.set('city', filterCity);
        if (filterHasPhone !== null) params.set('has_phone', filterHasPhone.toString());
        if (filterHasEmail !== null) params.set('has_email', filterHasEmail.toString());
        if (filterValidation) params.set('validation_status', filterValidation);

        const data = await apiClient.get<Lead[]>(`/leads?${params}`);
        allLeads.push(...data);
        if (data.length < limit) hasMore = false;
        else offset += limit;
      }

      setLeads(allLeads);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads');
    } finally {
      setLoading(false);
    }
  }, [searchId, filterMinScore, filterMaxScore, filterIndustry, filterCity, filterHasPhone, filterHasEmail, filterValidation]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);
  useEffect(() => { setPage(1); }, [filterMinScore, filterMaxScore, filterIndustry, filterCity, filterHasPhone, filterHasEmail, filterValidation]);

  const sourceBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const l of leads) {
      const src = l.source || 'unknown';
      counts[src] = (counts[src] || 0) + 1;
    }
    return counts;
  }, [leads]);

  const totalPages = Math.ceil(leads.length / pageSize);
  const paginatedLeads = leads.slice((page - 1) * pageSize, page * pageSize);

  const activeFilterCount = [filterMinScore, filterMaxScore, filterIndustry, filterCity, filterHasPhone, filterHasEmail, filterValidation].filter(f => f !== '' && f !== null).length;

  function buildExportUrl(): string {
    const params = new URLSearchParams();
    if (filterMinScore) params.set('min_score', filterMinScore);
    if (filterMaxScore) params.set('max_score', filterMaxScore);
    if (filterIndustry) params.set('industry', filterIndustry);
    if (filterCity) params.set('city', filterCity);
    if (filterHasPhone !== null) params.set('has_phone', filterHasPhone!.toString());
    if (filterHasEmail !== null) params.set('has_email', filterHasEmail!.toString());
    if (filterValidation) params.set('validation_status', filterValidation);
    return `${import.meta.env.VITE_API_URL || '/api'}/level7/export/csv?${params}`;
  }

  function handleExport() {
    const token = localStorage.getItem('vallg_token');
    fetch(buildExportUrl(), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Export failed');
        return res.blob();
      })
      .then((blob) => {
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `vallg_leads_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(blobUrl);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Export failed'));
  }

  function clearFilters() {
    setFilterMinScore('');
    setFilterMaxScore('');
    setFilterIndustry('');
    setFilterCity('');
    setFilterHasPhone(null);
    setFilterHasEmail(null);
    setFilterValidation('');
  }

  return (
    <div>
      <PageHeader
        title={searchQuery ? `Results for "${searchQuery}"` : "Results"}
        description={`${leads.length} scored leads`}
        actions={
          <div className="flex gap-2">
            {leads.length > 0 && (
              <Link
                to="/maps"
                className="inline-flex items-center gap-2 px-4 py-2 bg-dark-700 text-dark-100 text-sm font-medium rounded-lg border border-dark-500 hover:border-brand-500/50 hover:bg-brand-600/10 transition-all duration-150"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503-11.953a7.5 7.5 0 0 0-7.506 0M12 2.25l6.75 3-6.75 3-6.75-3 6.75-3Z" />
                </svg>
                View on Map
              </Link>
            )}
            {leads.length > 0 && (
              <Button variant="secondary" onClick={handleExport} icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
              }>
                Export CSV
              </Button>
            )}
            <Link
              to="/search"
              className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-500 transition-colors shadow-[0_1px_4px_rgba(91,91,214,0.4)]"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New Search
            </Link>
          </div>
        }
      />

      {/* Source breakdown */}
      {leads.length > 0 && Object.keys(sourceBreakdown).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(sourceBreakdown).sort((a, b) => b[1] - a[1]).map(([src, count]) => (
            <span key={src} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border bg-dark-700 border-dark-500 text-dark-200">
              <SourceBadge source={src} />
              <span className="font-bold">{count}</span>
            </span>
          ))}
        </div>
      )}

      {/* Filters */}
      {leads.length > 0 && (
        <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-end gap-3 mb-4 p-3 bg-dark-800 border border-dark-600 rounded-lg">
          <div className="flex-1 min-w-0 sm:min-w-[120px]">
            <label className="block text-xs font-medium text-dark-300 mb-1">Min Score</label>
            <input
              type="number"
              value={filterMinScore}
              onChange={(e) => setFilterMinScore(e.target.value)}
              placeholder="0"
              min="0"
              max="100"
              className="w-full px-3 py-1.5 text-sm bg-dark-700 border border-dark-500 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="flex-1 min-w-0 sm:min-w-[120px]">
            <label className="block text-xs font-medium text-dark-300 mb-1">Max Score</label>
            <input
              type="number"
              value={filterMaxScore}
              onChange={(e) => setFilterMaxScore(e.target.value)}
              placeholder="100"
              min="0"
              max="100"
              className="w-full px-3 py-1.5 text-sm bg-dark-700 border border-dark-500 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="flex-1 min-w-0 sm:min-w-[140px]">
            <label className="block text-xs font-medium text-dark-300 mb-1">Industry</label>
            <input
              type="text"
              value={filterIndustry}
              onChange={(e) => setFilterIndustry(e.target.value)}
              placeholder="e.g. Healthcare"
              className="w-full px-3 py-1.5 text-sm bg-dark-700 border border-dark-500 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="flex-1 min-w-0 sm:min-w-[120px]">
            <label className="block text-xs font-medium text-dark-300 mb-1">City</label>
            <input
              type="text"
              value={filterCity}
              onChange={(e) => setFilterCity(e.target.value)}
              placeholder="e.g. Hyderabad"
              className="w-full px-3 py-1.5 text-sm bg-dark-700 border border-dark-500 rounded-lg text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="flex-1 min-w-0 sm:min-w-[130px]">
            <label className="block text-xs font-medium text-dark-300 mb-1">Validation</label>
            <select
              value={filterValidation}
              onChange={(e) => setFilterValidation(e.target.value)}
              className="w-full px-3 py-1.5 text-sm bg-dark-700 border border-dark-500 rounded-lg text-dark-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">All</option>
              <option value="VALID">Valid</option>
              <option value="INVALID">Invalid</option>
              <option value="UNKNOWN">Unknown</option>
            </select>
          </div>
          <label className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 border border-dark-500 rounded-lg cursor-pointer hover:border-brand-500/50 transition-all text-sm">
            <input
              type="checkbox"
              checked={filterHasPhone === true}
              onChange={(e) => setFilterHasPhone(e.target.checked ? true : null)}
              className="w-3.5 h-3.5 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
            />
            <span className="text-dark-100">Has Phone</span>
          </label>
          <label className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 border border-dark-500 rounded-lg cursor-pointer hover:border-brand-500/50 transition-all text-sm">
            <input
              type="checkbox"
              checked={filterHasEmail === true}
              onChange={(e) => setFilterHasEmail(e.target.checked ? true : null)}
              className="w-3.5 h-3.5 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
            />
            <span className="text-dark-100">Has Email</span>
          </label>
          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="px-3 py-1.5 text-xs font-medium text-dark-300 hover:text-dark-100 transition-colors"
            >
              Clear ({activeFilterCount})
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="p-4 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : leads.length === 0 ? (
        <Card>
          <EmptyState
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v.375" />
              </svg>
            }
            title="No leads found"
            description="Run a search to start finding B2B leads. The pipeline extracts, cleans, validates, enriches, and scores leads automatically."
            action={
              <Link to="/search" className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-500 transition-colors">
                Start a search
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          <div className="text-xs text-dark-300 mb-2">
            Showing {paginatedLeads.length} of {leads.length} leads
          </div>
          <Card className="animate-fade-in overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-dark-600">
                <thead className="bg-dark-850">
                  <tr>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Score</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Business</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Location</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Phone</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Website</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Rating</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Source</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Validation</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-700">
                  {paginatedLeads.map((lead, i) => {
                    const location = [lead.city, lead.state].filter(Boolean).join(', ');
                    return (
                      <tr key={lead.id} className="hover:bg-dark-700/50 transition-colors" style={{ animationDelay: `${i * 20}ms` }}>
                        <td className="px-3 py-3">
                          <ScoreBadge score={lead.total_score} />
                        </td>
                        <td className="px-3 py-3">
                          <div className="text-sm font-medium text-dark-100 max-w-[200px] truncate">{lead.name || '—'}</div>
                          {lead.industry && (
                            <div className="text-xs text-dark-300 max-w-[200px] truncate">{lead.industry}</div>
                          )}
                        </td>
                        <td className="px-3 py-3 text-sm text-dark-200 max-w-[180px] truncate" title={lead.address || location}>
                          {location || '—'}
                        </td>
                        <td className="px-3 py-3 text-sm text-dark-200 whitespace-nowrap">{lead.phone || '—'}</td>
                        <td className="px-3 py-3 text-sm">
                          {lead.website ? (
                            <a
                              href={lead.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-brand-400 hover:text-brand-300 font-medium"
                            >
                              {(() => { try { return new URL(lead.website).hostname; } catch { return lead.website; } })()}
                            </a>
                          ) : (
                            <span className="text-dark-300">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-sm text-dark-200 whitespace-nowrap">
                          {lead.rating != null ? (
                            <span className="inline-flex items-center gap-1">
                              <svg className="w-4 h-4 text-amber-400 fill-amber-400" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                              </svg>
                              {lead.rating}
                              {lead.review_count != null && (
                                <span className="text-dark-300 text-xs">({lead.review_count})</span>
                              )}
                            </span>
                          ) : (
                            <span className="text-dark-300">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <SourceBadge source={lead.source} />
                        </td>
                        <td className="px-3 py-3">
                          <ValidationBadge status={lead.validation_status} />
                        </td>
                        <td className="px-3 py-3 text-sm">
                          <div className="flex items-center gap-2">
                            {lead.latitude && lead.longitude && (
                              <a
                                href={`https://www.google.com/maps/dir/?api=1&destination=${lead.latitude},${lead.longitude}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-emerald-400 hover:text-emerald-300 font-medium"
                                title="Get Directions"
                              >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503-11.953a7.5 7.5 0 0 0-7.506 0M12 2.25l6.75 3-6.75 3-6.75-3 6.75-3Z" />
                                </svg>
                              </a>
                            )}
                            <Link
                              to={`/results/${lead.id}`}
                              className="text-brand-400 hover:text-brand-300 font-medium"
                            >
                              View
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4">
              <div className="text-sm text-dark-200">
                Page <span className="font-medium text-dark-100">{page}</span> of <span className="font-medium text-dark-100">{totalPages}</span>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => setPage(page - 1)} disabled={page <= 1}>Previous</Button>
                <Button variant="secondary" size="sm" onClick={() => setPage(page + 1)} disabled={page >= totalPages}>Next</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
