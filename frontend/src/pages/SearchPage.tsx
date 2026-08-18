/**
 * url: /frontend/src/pages/SearchPage.tsx
 * About:
 *   Search page for ValLG. Simple search form asking only for
 *   search intent: what, city, state, industry. Automatically
 *   searches all configured sources. No filters or limits.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, CardContent, Button, Input, PageHeader } from '../components/ui';

const TEMPLATES = [
  { name: 'Hospitals — Eluru', query: 'Hospitals in Eluru', city: 'Eluru', state: 'Andhra Pradesh', icon: '🏥' },
  { name: 'Hospitals — Hyderabad', query: 'Hospitals in Hyderabad', city: 'Hyderabad', state: 'Telangana', icon: '🏥' },
  { name: 'IT Companies — Bangalore', query: 'IT services companies in Bangalore', city: 'Bangalore', state: 'Karnataka', icon: '💻' },
  { name: 'Manufacturing — Pune', query: 'Manufacturing companies in Pune', city: 'Pune', state: 'Maharashtra', icon: '🏭' },
  { name: 'Pharma — Hyderabad', query: 'Pharmaceutical companies in Hyderabad', city: 'Hyderabad', state: 'Telangana', icon: '💊' },
  { name: 'Startups — Bangalore', query: 'Startups in Bangalore', city: 'Bangalore', state: 'Karnataka', icon: '🚀' },
  { name: 'Restaurants — Vijayawada', query: 'Restaurants in Vijayawada', city: 'Vijayawada', state: 'Andhra Pradesh', icon: '🍽️' },
  { name: 'Consulting — Delhi NCR', query: 'Consulting firms in Delhi NCR', city: 'Delhi NCR', state: 'Delhi', icon: '📊' },
];

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function applyTemplate(template: (typeof TEMPLATES)[number]) {
    setQuery(template.query);
    setCity(template.city);
    setState(template.state);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const location = [city.trim(), state.trim()].filter(Boolean).join(', ') || undefined;
      const body = {
        query: query.trim(),
        location,
      };
      const res = await apiClient.post<{ pipeline_run: { id: string; status: string } }>('/search', body);
      navigate('/results', { state: { searchId: res.pipeline_run.id, query: query.trim() } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader
        title="Search Leads"
        description="Find businesses and decision-makers across India"
      />

      {/* Templates */}
      <div className="mb-6">
        <p className="text-xs font-semibold text-dark-300 uppercase tracking-wider mb-3">Quick start</p>
        <div className="flex flex-wrap gap-2">
          {TEMPLATES.map((template) => (
            <button
              key={template.name}
              onClick={() => applyTemplate(template)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-dark-800 border border-dark-600 text-dark-100 rounded-lg hover:border-brand-500/50 hover:bg-brand-600/10 hover:text-brand-300 transition-all duration-150 shadow-sm"
            >
              <span>{template.icon}</span>
              {template.name}
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
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g. "hospitals in Eluru"'
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
              }
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="City"
                id="city"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Eluru"
              />
              <Input
                label="State"
                id="state"
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                placeholder="Andhra Pradesh"
              />
            </div>

            <div className="p-3 bg-dark-800 border border-dark-600 rounded-lg">
              <p className="text-xs text-dark-300">
                Searches all available sources automatically: Google Maps, OpenStreetMap, Web Search, IndiaMART, JustDial. Results include every record found with clear source attribution.
              </p>
            </div>

            <div className="pt-1">
              <Button
                type="submit"
                size="lg"
                loading={submitting}
                className="w-full"
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                  </svg>
                }
              >
                {submitting ? 'Searching all sources...' : 'Search'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
