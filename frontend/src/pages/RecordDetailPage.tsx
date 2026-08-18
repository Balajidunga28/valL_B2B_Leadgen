/**
 * url: /frontend/src/pages/RecordDetailPage.tsx
 * About:
 *   Lead detail page for ValLG. Displays complete lead data including
 *   company info, location, rating, source, validation, enrichment,
 *   and score breakdown. Uses the unified /api/leads/{id} endpoint.
 */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, CardHeader, CardContent, Badge, Skeleton } from '../components/ui';
import type { Lead } from '../types';

function DetailRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 py-2.5 border-b border-dark-600 last:border-0">
      <dt className="text-xs font-semibold text-dark-300 uppercase tracking-wider sm:w-40 shrink-0">{label}</dt>
      <dd className={`text-sm text-dark-100 ${mono ? 'font-mono text-xs break-all text-dark-200' : ''}`}>
        {value || <span className="text-dark-500">—</span>}
      </dd>
    </div>
  );
}

const SOURCE_MAP: Record<string, string> = {
  google_search: 'Google Maps',
  google_places: 'Google Places',
  openstreetmap: 'OpenStreetMap',
  web_search: 'Web Search',
  indiamart: 'IndiaMART',
  justdial: 'JustDial',
};

export default function RecordDetailPage() {
  const { recordId } = useParams<{ recordId: string }>();
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!recordId) return;
    async function fetchLead() {
      try {
        const data = await apiClient.get<Lead>(`/leads/${recordId}`);
        setLead(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lead');
      } finally {
        setLoading(false);
      }
    }
    fetchLead();
  }, [recordId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">{error}</div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-12">
        <div className="w-12 h-12 rounded-xl bg-dark-700 border border-dark-600 flex items-center justify-center text-dark-300 mx-auto mb-4">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
        </div>
        <p className="text-sm text-dark-200">Lead not found.</p>
      </div>
    );
  }

  const scoreColor = (s: number) => s >= 60 ? 'text-emerald-400' : s >= 35 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="animate-fade-in">
      {/* Navigation & Title */}
      <div className="mb-6">
        <Link
          to="/results"
          className="inline-flex items-center gap-1.5 text-sm text-dark-200 hover:text-dark-100 transition-colors mb-3"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Results
        </Link>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {lead.name || 'Unnamed Lead'}
          </h1>
          <div className="flex items-center gap-2 sm:gap-3 mt-2 flex-wrap">
              {lead.source && <Badge variant="brand">{SOURCE_MAP[lead.source] || lead.source}</Badge>}
              {lead.validation_status && (
                <Badge variant={lead.validation_status === 'VALID' ? 'success' : lead.validation_status === 'INVALID' ? 'error' : 'default'}>
                  {lead.validation_status}
                </Badge>
              )}
              {lead.total_score != null && (
                <span className={`text-sm font-semibold ${scoreColor(lead.total_score)}`}>
                  Score: {lead.total_score.toFixed(1)}
                </span>
              )}
            </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Company Info */}
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
              </svg>
              Company Information
            </h2>
          </CardHeader>
          <CardContent>
            <dl>
              <DetailRow label="Name" value={lead.name} />
              <DetailRow label="Industry" value={lead.industry} />
              <DetailRow label="Phone" value={lead.phone} />
              <DetailRow label="Email" value={lead.enrichment_email} />
              <DetailRow label="Website" value={lead.website ? <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300 underline underline-offset-2">{lead.website}</a> : null} />
            </dl>
          </CardContent>
        </Card>

        {/* Location & Rating */}
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
              </svg>
              Location & Rating
            </h2>
          </CardHeader>
          <CardContent>
            <dl>
              <DetailRow label="Address" value={lead.address} />
              <DetailRow label="City" value={lead.city} />
              <DetailRow label="State" value={lead.state} />
              <DetailRow label="Country" value={lead.country} />
              <DetailRow label="Latitude" value={lead.latitude} mono />
              <DetailRow label="Longitude" value={lead.longitude} mono />
              <DetailRow
                label="Rating"
                value={
                  lead.rating != null ? (
                    <span className="inline-flex items-center gap-1.5">
                      <svg className="w-4 h-4 text-amber-400 fill-amber-400" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="font-medium text-dark-100">{lead.rating}</span>
                      {lead.review_count != null && <span className="text-dark-300 text-xs">({lead.review_count} reviews)</span>}
                    </span>
                  ) : null
                }
              />
              {lead.latitude && lead.longitude && (
                <DetailRow
                  label="Directions"
                  value={<a href={`https://www.google.com/maps/dir/?api=1&destination=${lead.latitude},${lead.longitude}`} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300 underline underline-offset-2">Open in Google Maps</a>}
                />
              )}
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Score Breakdown */}
      {lead.total_score != null && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              Score Breakdown
            </h2>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {[
                { label: 'Total Score', value: lead.total_score, max: 100 },
              ].map((item) => (
                <div key={item.label} className="text-center p-3 bg-dark-800 rounded-lg border border-dark-600">
                  <div className={`text-2xl font-bold ${scoreColor(item.value)}`}>{item.value.toFixed(1)}</div>
                  <div className="text-xs text-dark-300 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-dark-400">
              Score version: {lead.score_version || 'N/A'}
              {lead.scored_at && <> | Scored at: {new Date(lead.scored_at).toLocaleString()}</>}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Enrichment */}
      {lead.enrichment_description && (
        <Card className="mb-6">
          <CardHeader>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
              </svg>
              Enrichment
            </h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-dark-200 leading-relaxed">{lead.enrichment_description}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
