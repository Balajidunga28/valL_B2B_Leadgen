/**
 * url: /frontend/src/pages/DirectoriesPage.tsx
 * About:
 *   Directory discovery page for ValLG. Provides a search interface
 *   pre-configured with business directory sources (JustDial, IndiaMART,
 *   Yellow Pages, Sulekha, TradeIndia). Reuses the same canonical lead
 *   pipeline as Search — candidates go through collection, validation,
 *   location verification, deduplication, and enrichment.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, CardContent, Button, Input, PageHeader } from '../components/ui';

const DIRECTORY_SOURCES = [
  {
    id: 'indiamart',
    name: 'IndiaMART',
    description: "India's largest B2B marketplace — product/service listings and supplier details.",
    status: 'active' as const,
  },
  {
    id: 'justdial',
    name: 'JustDial',
    description: 'Local business directory — phone numbers, addresses, and ratings.',
    status: 'available' as const,
  },
  {
    id: 'web_search',
    name: 'Yellow Pages',
    description: 'Discovers Yellow Pages listings via web search results.',
    status: 'active' as const,
  },
  {
    id: 'sulekha',
    name: 'Sulekha',
    description: 'Service directory for local businesses across India.',
    status: 'unavailable' as const,
  },
  {
    id: 'tradeindia',
    name: 'TradeIndia',
    description: 'B2B trade portal — manufacturer and supplier directory.',
    status: 'unavailable' as const,
  },
];

const CATEGORY_TEMPLATES = [
  { name: 'Hospitals', query: 'Hospitals', icon: '🏥' },
  { name: 'Pharmaceuticals', query: 'Pharmaceutical companies', icon: '💊' },
  { name: 'IT Services', query: 'IT services companies', icon: '💻' },
  { name: 'Manufacturing', query: 'Manufacturing companies', icon: '🏭' },
  { name: 'Consulting', query: 'Consulting firms', icon: '📊' },
  { name: 'Education', query: 'Educational institutions', icon: '🎓' },
];

export default function DirectoriesPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [maxLeads, setMaxLeads] = useState(100);
  const [selectedSources, setSelectedSources] = useState<string[]>(['indiamart', 'justdial', 'web_search']);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function toggleSource(sourceId: string) {
    setSelectedSources((prev) =>
      prev.includes(sourceId) ? prev.filter((s) => s !== sourceId) : [...prev, sourceId]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    if (selectedSources.length === 0) {
      setError('Select at least one directory source');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const location = [city.trim(), state.trim()].filter(Boolean).join(', ') || undefined;
      const body = {
        query: query.trim(),
        location,
        sources: selectedSources,
        limit: Math.min(Math.max(parseInt(String(maxLeads)) || 100, 1), 200),
      };
      const result = await apiClient.post<{ pipeline_run: { id: string; status: string; total_extracted: number; error_message: string | null } }>('/search', body);
      navigate(`/results?run=${result.pipeline_run.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Directory search failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader
        title="Business Directories"
        description="Discover businesses from India's leading B2B directories"
      />

      {/* Directory status cards */}
      <div className="mb-6">
        <p className="text-xs font-semibold text-dark-300 uppercase tracking-wider mb-3">Directory Providers</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {DIRECTORY_SOURCES.map((src) => (
            <div
              key={src.id}
              className={`px-3 py-2 rounded-lg border transition-all ${
                src.status === 'active'
                  ? 'bg-emerald-500/5 border-emerald-500/20'
                  : src.status === 'available'
                  ? 'bg-blue-500/5 border-blue-500/20'
                  : 'bg-dark-800 border-dark-600 opacity-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${
                  src.status === 'active' ? 'bg-emerald-400' : src.status === 'available' ? 'bg-blue-400' : 'bg-dark-400'
                }`} />
                <span className="text-xs font-medium text-dark-100">{src.name}</span>
                <span className={`text-[9px] font-medium px-1 py-0.5 rounded ${
                  src.status === 'active' ? 'bg-emerald-500/20 text-emerald-300' :
                  src.status === 'available' ? 'bg-blue-500/20 text-blue-300' :
                  'bg-dark-700 text-dark-400'
                }`}>
                  {src.status === 'active' ? 'Active' : src.status === 'available' ? 'Available' : 'Unavailable'}
                </span>
              </div>
              <p className="text-[10px] text-dark-300 mt-0.5">{src.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Category templates */}
      <div className="mb-6">
        <p className="text-xs font-semibold text-dark-300 uppercase tracking-wider mb-3">Quick categories</p>
        <div className="flex flex-wrap gap-2">
          {CATEGORY_TEMPLATES.map((cat) => (
            <button
              key={cat.name}
              onClick={() => setQuery(cat.query)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-dark-800 border border-dark-600 text-dark-100 rounded-lg hover:border-brand-500/50 hover:bg-brand-600/10 hover:text-brand-300 transition-all duration-150"
            >
              <span>{cat.icon}</span>
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* Search form */}
      <Card>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 animate-scale-in">
                {error}
              </div>
            )}

            <Input
              label="What are you looking for?"
              id="dir-query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g. "hospitals in Hyderabad"'
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                </svg>
              }
            />

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
              <Input
                label="City"
                id="dir-city"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Hyderabad"
              />
              <Input
                label="State"
                id="dir-state"
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                placeholder="Telangana"
              />
              <Input
                label="Max Leads"
                id="dir-maxLeads"
                type="number"
                min={1}
                max={200}
                value={maxLeads}
                onChange={(e) => setMaxLeads(parseInt(e.target.value) || 100)}
                placeholder="100"
              />
              <div className="flex items-end">
                <Button
                  type="submit"
                  loading={submitting}
                  className="w-full"
                  icon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
                    </svg>
                  }
                >
                  {submitting ? 'Searching...' : 'Search Directories'}
                </Button>
              </div>
            </div>

            {/* Source selection */}
            <div>
              <label className="block text-sm font-medium text-dark-100 mb-2.5">Directory Sources</label>
              <div className="flex flex-wrap gap-2">
                {DIRECTORY_SOURCES.map((src) => {
                  const isSelected = selectedSources.includes(src.id);
                  const isDisabled = src.status === 'unavailable';
                  return (
                    <label
                      key={src.id}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all text-sm ${
                        isDisabled
                          ? 'bg-dark-800 border-dark-600 opacity-50 cursor-not-allowed'
                          : isSelected
                          ? 'bg-brand-600/10 border-brand-500/30 text-brand-300 cursor-pointer'
                          : 'bg-dark-700 border-dark-500 text-dark-100 cursor-pointer hover:border-brand-500/50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={isDisabled}
                        onChange={() => toggleSource(src.id)}
                        className="w-3.5 h-3.5 rounded border-dark-400 text-brand-500 focus:ring-brand-500 bg-dark-600"
                      />
                      <span className="font-medium">{src.name}</span>
                      {src.status === 'unavailable' && (
                        <span className="text-[9px] text-dark-400">(unavailable)</span>
                      )}
                    </label>
                  );
                })}
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="mt-4 p-3 bg-dark-800 border border-dark-600 rounded-lg">
        <p className="text-xs text-dark-300">
          Results from directory searches go through the same pipeline as Search — entity resolution, location validation, deduplication, and enrichment. If a business already exists from Google Maps, OpenStreetMap, or any other source, the directory data merges into the existing canonical lead.
        </p>
      </div>
    </div>
  );
}
