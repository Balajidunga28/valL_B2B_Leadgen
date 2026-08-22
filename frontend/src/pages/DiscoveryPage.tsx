/**
 * url: /frontend/src/pages/DiscoveryPage.tsx
 * About:
 *   Discovery page for ValLG. Allows users to search for businesses
 *   using Google Maps as the discovery source. Connects to the existing
 *   search API, polls for results, and displays them in a clean, responsive table.
 *   Includes "Save as Lead" action to save discovered businesses to the lead management system.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiClient, downloadFile } from '../api/client';
import { Card, CardContent, Button, Input, PageHeader, EmptyState, Badge } from '../components/ui';
import type { Lead } from '../types';

const GOOGLE_MAPS_SOURCE = 'google_maps_scraper';
const WEB_SEARCH_SOURCE = 'web_search';
const INDIAMART_SOURCE = 'indiamart';
const JUSTDIAL_SOURCE = 'justdial';
const OPENSTREETMAP_SOURCE = 'openstreetmap';
const POLL_INTERVAL = 2000;
const MAX_POLL_ATTEMPTS = 60;

interface LeadSaveState {
  saving: boolean;
  saved: boolean;
  error: string | null;
}

export default function DiscoveryPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [query, setQuery] = useState('');
  const [locationInput, setLocationInput] = useState('');
  const [maxResults, setMaxResults] = useState(50);
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set([GOOGLE_MAPS_SOURCE, WEB_SEARCH_SOURCE, OPENSTREETMAP_SOURCE]));
  const [searching, setSearching] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<Lead[]>([]);
  const [searchCompleted, setSearchCompleted] = useState(false);
  const [pollAttempts, setPollAttempts] = useState(0);
  const [searchId, setSearchId] = useState<string | null>(null);
  const [leadSaveStates, setLeadSaveStates] = useState<Record<string, LeadSaveState>>({});

  const pollTimeoutRef = useRef<number | null>(null);

  // Get search query from URL state if navigated from search
  const initialQuery = (location.state as { query?: string })?.query || '';
  const initialLocation = (location.state as { location?: string })?.location || '';

  // Initialize with URL state if available
  if (initialQuery && !query) {
    setQuery(initialQuery);
  }
  if (initialLocation && !locationInput) {
    setLocationInput(initialLocation);
  }

  function handleSourceToggle(source: string) {
    setSelectedSources(prev => {
      const next = new Set(prev);
      if (next.has(source)) {
        next.delete(source);
      } else {
        next.add(source);
      }
      return next;
    });
  }

  function validateForm(): boolean {
    if (!query.trim()) {
      setError('Search query cannot be empty');
      return false;
    }
    if (selectedSources.size === 0) {
      setError('Please select at least one source');
      return false;
    }
    if (maxResults < 1 || maxResults > 200) {
      setError('Maximum results must be between 1 and 200');
      return false;
    }
    return true;
  }

  const fetchResults = useCallback(async (runId: string) => {
    try {
      const params = new URLSearchParams({
        search_id: runId,
        limit: '200',
        offset: '0',
      });
      const data = await apiClient.get<Lead[]>(`/leads?${params}`);
      return data;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to fetch results');
    }
  }, []);

  const pollForResults = useCallback(async (runId: string) => {
    if (pollAttempts >= MAX_POLL_ATTEMPTS) {
      setPolling(false);
      setError('Search is taking longer than expected. Please check the Results page.');
      return;
    }

    try {
      const leads = await fetchResults(runId);
      if (leads.length > 0) {
        setResults(leads);
        // Initialize save states for new leads
        const newSaveStates: Record<string, LeadSaveState> = {};
        leads.forEach(lead => {
          newSaveStates[lead.id] = { saving: false, saved: lead.is_saved, error: null };
        });
        setLeadSaveStates(prev => ({ ...prev, ...newSaveStates }));
        setPolling(false);
        setSearchCompleted(true);
        return;
      }
    } catch (err) {
      // Ignore errors during polling, just continue
      console.debug('Polling error:', err);
    }

    setPollAttempts((prev) => prev + 1);
    pollTimeoutRef.current = window.setTimeout(() => {
      pollForResults(runId);
    }, POLL_INTERVAL);
  }, [fetchResults, pollAttempts]);

  const startPolling = useCallback((runId: string) => {
    setSearchId(runId);
    setPolling(true);
    setPollAttempts(0);
    pollForResults(runId);
  }, [pollForResults]);

  const stopPolling = useCallback(() => {
    setPolling(false);
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validateForm()) return;

    setError('');
    setSearching(true);
    setSearchCompleted(false);
    setResults([]);

    try {
      const body = {
        query: query.trim(),
        location: locationInput.trim() || undefined,
        sources: Array.from(selectedSources),
        limit: maxResults,
      };

      const res = await apiClient.post<{ pipeline_run: { id: string; status: string } }>('/search', body);
      const runId = res.pipeline_run.id;

      // Start polling for results
      startPolling(runId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Please try again.');
      setSearching(false);
    }
  }

  async function handleSaveAsLead(lead: Lead) {
    if (!searchId) {
      setLeadSaveStates(prev => ({
        ...prev,
        [lead.id]: { ...prev[lead.id], error: 'Search ID not available' },
      }));
      return;
    }

    // Update state to saving
    setLeadSaveStates(prev => ({
      ...prev,
      [lead.id]: { saving: true, saved: false, error: null },
    }));

    try {
      await apiClient.post('/leads', {
        company_id: lead.id,
        pipeline_run_id: searchId,
        // raw_record_id will be auto-resolved by backend
      });

      // Update lead in results to mark as saved
      setResults(prev => prev.map(l => l.id === lead.id ? { ...l, is_saved: true } : l));
      setLeadSaveStates(prev => ({
        ...prev,
        [lead.id]: { saving: false, saved: true, error: null },
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save lead';
      setLeadSaveStates(prev => ({
        ...prev,
        [lead.id]: { saving: false, saved: false, error: errorMessage },
      }));
    }
  }

  async function handleExport() {
    if (!searchId) {
      setError('Search ID not available for export');
      return;
    }

    // Run export in background — don't block the page
    try {
      downloadFile(`/api/export/csv?pipeline_run_id=${searchId}`, `vallg_discovery_${new Date().toISOString().slice(0, 10)}.csv`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  }

  function handleClear() {
    setQuery('');
    setLocationInput('');
    setMaxResults(50);
    setError('');
    setResults([]);
    setSearchCompleted(false);
    setSearchId(null);
    setSearching(false);
    setLeadSaveStates({});
    stopPolling();
  }

  const hasResults = results.length > 0;
  const isLoading = searching || polling;

  return (
    <div className="max-w-5xl mx-auto">
      <PageHeader
        title="Business Discovery"
        description="Search for businesses using natural language — find restaurants, hotels, IT companies, and more across multiple sources"
      />

      {/* Search Form */}
      <Card className="mb-6">
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 animate-scale-in">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Search Query"
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='e.g. "restaurants in Johannesburg" or "IT companies Hyderabad"'
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                  </svg>
                }
                disabled={isLoading}
              />

              <Input
                label="Location (optional)"
                id="location"
                type="text"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder='e.g. "Johannesburg" — extracted from query if omitted'
                hint="Location is auto-detected from query when possible"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                }
                disabled={isLoading}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-100 mb-1.5">Sources</label>
                <div className="p-3 bg-dark-700 border border-dark-500 rounded-lg space-y-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.has(GOOGLE_MAPS_SOURCE)}
                      onChange={() => handleSourceToggle(GOOGLE_MAPS_SOURCE)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                    />
                    <span className="text-dark-100 font-medium">Google Maps</span>
                    <Badge variant="brand" className="ml-auto">Primary</Badge>
                  </label>
                  <p className="text-xs text-dark-300 ml-6">Business listings with reviews, ratings, and contact info</p>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.has(WEB_SEARCH_SOURCE)}
                      onChange={() => handleSourceToggle(WEB_SEARCH_SOURCE)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                    />
                    <span className="text-dark-100 font-medium">Web Search (Bing)</span>
                    <Badge variant="subtle" className="ml-auto">Secondary</Badge>
                  </label>
                  <p className="text-xs text-dark-300 ml-6">Business listings discovered through web search results</p>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.has(INDIAMART_SOURCE)}
                      onChange={() => handleSourceToggle(INDIAMART_SOURCE)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                    />
                    <span className="text-dark-100 font-medium">IndiaMART</span>
                    <Badge variant="subtle" className="ml-auto">Directory</Badge>
                  </label>
                  <p className="text-xs text-dark-300 ml-6">India's largest B2B marketplace directory</p>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.has(JUSTDIAL_SOURCE)}
                      onChange={() => handleSourceToggle(JUSTDIAL_SOURCE)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                    />
                    <span className="text-dark-100 font-medium">JustDial</span>
                    <Badge variant="subtle" className="ml-auto">Directory</Badge>
                  </label>
                  <p className="text-xs text-dark-300 ml-6">Local business directory for India</p>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedSources.has(OPENSTREETMAP_SOURCE)}
                      onChange={() => handleSourceToggle(OPENSTREETMAP_SOURCE)}
                      disabled={isLoading}
                      className="w-4 h-4 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                    />
                    <span className="text-dark-100 font-medium">OpenStreetMap</span>
                    <Badge variant="subtle" className="ml-auto">Free</Badge>
                  </label>
                  <p className="text-xs text-dark-300 ml-6">Open-source map data with global business listings</p>
                </div>
              </div>

              <Input
                label="Maximum Results"
                id="maxResults"
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 50)}
                placeholder="50"
                min="1"
                max="200"
                hint="Maximum number of results to fetch (1-200)"
                disabled={isLoading}
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                type="submit"
                size="lg"
                loading={isLoading}
                className="flex-1"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                  </svg>
                }
              >
                {searching ? 'Starting search...' : polling ? 'Waiting for results...' : 'Start Discovery'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="lg"
                onClick={handleClear}
                disabled={isLoading}
                className="flex-1 sm:flex-none"
              >
                Clear
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Polling indicator */}
      {polling && (
        <div className="mb-4 p-3 bg-brand-600/10 border border-brand-500/30 rounded-lg animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <div className="flex-1">
              <p className="text-sm font-medium text-brand-300">
                Searching {Array.from(selectedSources).map(s => {
                  if (s === GOOGLE_MAPS_SOURCE) return 'Google Maps';
                  if (s === WEB_SEARCH_SOURCE) return 'Web Search';
                  if (s === INDIAMART_SOURCE) return 'IndiaMART';
                  if (s === JUSTDIAL_SOURCE) return 'JustDial';
                  if (s === OPENSTREETMAP_SOURCE) return 'OpenStreetMap';
                  return s;
                }).join(' + ')}...
              </p>
              <p className="text-xs text-dark-200">Query interpreted and searching across multiple sources for businesses matching your criteria</p>
            </div>
            <div className="w-48 h-2 bg-dark-700 rounded-full overflow-hidden">
              <div className="h-full bg-brand-500 animate-pulse" style={{ width: `${Math.min((pollAttempts / MAX_POLL_ATTEMPTS) * 100, 90)}%` }} />
            </div>
          </div>
        </div>
      )}

      {/* Results Section */}
      {(searchCompleted || hasResults) && (
        <div className="animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Results {hasResults && <span className="text-brand-400 font-mono">({results.length})</span>}
              </h2>
              {hasResults && (
                <p className="text-xs text-dark-300 mt-1">
                  Sources: {[...new Set(results.flatMap(r => r.sources))].map(s => {
                    if (s === GOOGLE_MAPS_SOURCE) return 'Google Maps';
                    if (s === WEB_SEARCH_SOURCE) return 'Web Search';
                    if (s === INDIAMART_SOURCE) return 'IndiaMART';
                    if (s === JUSTDIAL_SOURCE) return 'JustDial';
                    if (s === OPENSTREETMAP_SOURCE) return 'OpenStreetMap';
                    return s;
                  }).join(', ')}
                </p>
              )}
            </div>
            {hasResults && (
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={handleExport} disabled={!searchId}>
                  Export CSV
                </Button>
                <Button variant="secondary" size="sm" onClick={() => navigate('/results', { state: { searchId, query: query.trim() } })}>
                  View All Results
                </Button>
              </div>
            )}
          </div>

          {error && !hasResults && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 mb-4">
              {error}
            </div>
          )}

          {!error && !hasResults && (
            <Card>
              <EmptyState
                icon={
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
                title="No relevant results found"
                description="Try a more specific query or adjust the location. The system searches broadly but only returns businesses that match your criteria."
                action={
                  <Button variant="secondary" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                    Refine Search
                  </Button>
                }
              />
            </Card>
          )}

          {hasResults && (
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-dark-600">
                  <thead className="bg-dark-850">
                    <tr>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Business Name</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Address</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Phone</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Website</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Rating</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Reviews</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider">Source</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold text-dark-200 uppercase tracking-wider w-32">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-700">
                    {results.slice(0, 20).map((lead, i) => {
                      const saveState = leadSaveStates[lead.id] || { saving: false, saved: lead.is_saved, error: null };
                      return (
                        <tr key={lead.id} className="hover:bg-dark-700/50 transition-colors" style={{ animationDelay: `${i * 20}ms` }}>
                          <td className="px-3 py-3">
                            <div className="text-sm font-medium text-dark-100 max-w-[250px] truncate">{lead.name || '—'}</div>
                            {lead.industry && (
                              <div className="text-xs text-dark-300 max-w-[250px] truncate">{lead.industry}</div>
                            )}
                          </td>
                          <td className="px-3 py-3 text-sm text-dark-200 max-w-[200px] truncate" title={lead.address || ''}>
                            {[lead.city, lead.state].filter(Boolean).join(', ') || lead.address || '—'}
                          </td>
                          <td className="px-3 py-3 text-sm text-dark-200 whitespace-nowrap">{lead.phone || '—'}</td>
                          <td className="px-3 py-3 text-sm">
                            {lead.website ? (
                              <a
                                href={lead.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-brand-400 hover:text-brand-300 font-medium truncate block max-w-[150px]"
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
                              </span>
                            ) : (
                              <span className="text-dark-300">—</span>
                            )}
                          </td>
                          <td className="px-3 py-3 text-sm text-dark-200 whitespace-nowrap">
                            {lead.review_count != null ? lead.review_count : '—'}
                          </td>
                          <td className="px-3 py-3">
                            {(lead.sources && lead.sources.length > 0) ? (
                              <div className="flex flex-wrap gap-1">
                                {lead.sources.map((src, idx) => {
                                  if (src === WEB_SEARCH_SOURCE) {
                                    return <Badge key={idx} variant="subtle">Web Search</Badge>;
                                  }
                                  if (src === GOOGLE_MAPS_SOURCE) {
                                    return <Badge key={idx} variant="brand">Google Maps</Badge>;
                                  }
                                  if (src === INDIAMART_SOURCE) {
                                    return <Badge key={idx} variant="subtle">IndiaMART</Badge>;
                                  }
                                  if (src === JUSTDIAL_SOURCE) {
                                    return <Badge key={idx} variant="subtle">JustDial</Badge>;
                                  }
                                  return <Badge key={idx} variant="subtle">{src}</Badge>;
                                })}
                              </div>
                            ) : (
                              <span className="text-dark-300">—</span>
                            )}
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              {saveState.saved ? (
                                <Badge variant="success" className="flex items-center gap-1">
                                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                                  </svg>
                                  Saved
                                </Badge>
                              ) : (
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={() => handleSaveAsLead(lead)}
                                  disabled={saveState.saving}
                                  loading={saveState.saving}
                                  className="h-8"
                                >
                                  Save as Lead
                                </Button>
                              )}
                              {saveState.error && (
                                <span className="text-xs text-red-400 animate-fade-in">{saveState.error}</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {results.length > 20 && (
                <div className="p-4 border-t border-dark-600 bg-dark-800/50">
                  <p className="text-sm text-dark-300 text-center">
                    Showing 20 of {results.length} results. <span className="text-brand-400 font-medium">View All Results</span> to see more.
                  </p>
                </div>
              )}
            </Card>
          )}
        </div>
      )}
    </div>
  );
}