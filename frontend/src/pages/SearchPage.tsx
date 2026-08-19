/**
 * url: /frontend/src/pages/SearchPage.tsx
 * About:
 *   Search page for ValLG. Single natural-language search input.
 *   Backend dynamically extracts category and location from the query.
 *   No hardcoded cities, states, or default values.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, CardContent, Button, Input, PageHeader } from '../components/ui';

const TEMPLATES = [
  { name: 'Hospitals — Rajahmundry', query: 'hospitals in Rajahmundry', icon: '🏥' },
  { name: 'Restaurants — London', query: 'restaurants in London', icon: '🍽️' },
  { name: 'Startups — Kolkata', query: 'startups in Kolkata', icon: '🚀' },
  { name: 'Dentists — Toronto', query: 'dentists in Toronto', icon: '🦷' },
  { name: 'IT Companies — Bangalore', query: 'IT companies in Bangalore', icon: '💻' },
  { name: 'Pharma — Hyderabad', query: 'pharmaceutical companies in Hyderabad', icon: '💊' },
  { name: 'Manufacturing — Pune', query: 'manufacturing companies in Pune', icon: '🏭' },
  { name: 'Consulting — Delhi', query: 'consulting firms in Delhi', icon: '📊' },
];

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function applyTemplate(template: (typeof TEMPLATES)[number]) {
    setQuery(template.query);
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
      const body = {
        query: query.trim(),
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
        description="Find businesses and decision-makers worldwide"
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
              placeholder='e.g. "hospitals in Rajahmundry" or "restaurants in London"'
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
              }
            />

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
