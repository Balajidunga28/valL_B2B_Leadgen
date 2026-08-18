/**
 * url: /frontend/src/pages/SourcesPage.tsx
 * About:
 *   Sources page for ValLG. Displays all data providers with real-time
 *   statistics computed from actual raw_records and pipeline_runs.
 *   Shows status, candidates contributed, leads enriched, last run,
 *   and configuration status. No fabricated data.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, PageHeader, EmptyState, Skeleton } from '../components/ui';

interface SourceInfo {
  adapter_name: string;
  display_name: string;
  category: string;
  description: string;
  requires_api_key: boolean;
  free: boolean;
  status: 'active' | 'available' | 'not_configured' | 'unavailable';
  candidates_contributed: number;
  leads_enriched: number;
  total_runs: number;
  last_run_at: string | null;
  has_api_key: boolean;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  active: { label: 'Active', color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30', dot: 'bg-emerald-400' },
  available: { label: 'Available', color: 'bg-blue-500/15 text-blue-300 border-blue-500/30', dot: 'bg-blue-400' },
  not_configured: { label: 'Not Configured', color: 'bg-amber-500/15 text-amber-300 border-amber-500/30', dot: 'bg-amber-400' },
  unavailable: { label: 'Unavailable', color: 'bg-red-500/15 text-red-300 border-red-500/30', dot: 'bg-red-400' },
};

function formatDate(iso: string | null): string {
  if (!iso) return 'Never';
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { fetchSources(); }, []);

  async function fetchSources() {
    try {
      const data = await apiClient.get<{ sources: SourceInfo[] }>('/sources');
      setSources(data.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setLoading(false);
    }
  }

  const categories = [...new Set(sources.map((s) => s.category))];

  return (
    <div>
      <PageHeader
        title="Data Sources"
        description="All configured data providers and their current status"
      />

      {error && (
        <div className="p-4 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : sources.length === 0 ? (
        <Card>
          <EmptyState
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m9.444-3.875a4.5 4.5 0 0 0-1.242-7.244l-4.5-4.5a4.5 4.5 0 0 0-6.364 6.364L4.25 8.5" />
              </svg>
            }
            title="No sources found"
            description="Data sources will appear here once the pipeline is initialized."
          />
        </Card>
      ) : (
        categories.map((category) => (
          <div key={category} className="mb-6">
            <h3 className="text-xs font-semibold text-dark-300 uppercase tracking-wider mb-3">{category}</h3>
            <div className="space-y-2">
              {sources
                .filter((s) => s.category === category)
                .map((source) => {
                  const statusInfo = STATUS_CONFIG[source.status] || STATUS_CONFIG.available;
                  return (
                    <Card key={source.adapter_name} className="animate-fade-in">
                      <div className="px-5 py-4 flex items-center gap-4">
                        {/* Status dot */}
                        <div className={`w-2.5 h-2.5 rounded-full ${statusInfo.dot} flex-shrink-0`} />

                        {/* Main info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="text-sm font-semibold text-dark-100">{source.display_name}</span>
                            <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border ${statusInfo.color}`}>
                              {statusInfo.label}
                            </span>
                            {source.free && (
                              <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                Free
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-dark-300 truncate">{source.description}</p>
                        </div>

                        {/* Stats */}
                        <div className="flex items-center gap-6 text-right flex-shrink-0">
                          <div>
                            <div className="text-lg font-bold text-dark-100">{source.candidates_contributed}</div>
                            <div className="text-[10px] text-dark-400 uppercase">Candidates</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-dark-100">{source.leads_enriched}</div>
                            <div className="text-[10px] text-dark-400 uppercase">Enriched</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-dark-100">{source.total_runs}</div>
                            <div className="text-[10px] text-dark-400 uppercase">Runs</div>
                          </div>
                          <div className="w-24">
                            <div className="text-xs text-dark-200">{formatDate(source.last_run_at)}</div>
                            <div className="text-[10px] text-dark-400 uppercase">Last Run</div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  );
                })}
            </div>
          </div>
        ))
      )}

      {!loading && sources.length > 0 && (
        <div className="mt-6 flex gap-3">
          <Link
            to="/search"
            className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-500 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Run a Search
          </Link>
          <Link
            to="/settings"
            className="inline-flex items-center gap-2 px-4 py-2 bg-dark-700 text-dark-100 text-sm font-medium rounded-lg border border-dark-500 hover:border-brand-500/50 transition-all"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
            Configure API Keys
          </Link>
        </div>
      )}
    </div>
  );
}
