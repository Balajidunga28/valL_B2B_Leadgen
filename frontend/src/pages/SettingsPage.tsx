/**
 * url: /frontend/src/pages/SettingsPage.tsx
 * About:
 *   Settings page for ValLG dark theme. Manages API keys for data sources
 *   with dark card layout, elevated surfaces, and polished status indicators.
 *   Clear visual states for configured/unconfigured API keys.
 */

import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { Card, CardHeader, CardContent, Button, Input, Badge, PageHeader, Skeleton } from '../components/ui';

interface ApiKey {
  id: string;
  source_adapter: string;
  api_key_hint: string;
  status: string;
  last_verified_at: string | null;
  created_at: string;
}

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchKeys(); }, []);

  async function fetchKeys() {
    try {
      const data = await apiClient.get<{ keys: ApiKey[] }>('/settings/api-keys');
      setKeys(data.keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }

  async function handleAddKey() {
    if (!newKey.trim()) return;
    setSaving(true);
    setError('');
    try {
      await apiClient.post('/settings/api-keys', {
        source_adapter: 'google_places',
        api_key: newKey.trim(),
      });
      setNewKey('');
      setShowAddForm(false);
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteKey(keyId: string) {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    try {
      await apiClient.delete(`/settings/api-keys/${keyId}`);
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API key');
    }
  }

  const googlePlacesKey = keys.find((k) => k.source_adapter === 'google_places');

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure data sources and manage your account"
      />

      {error && (
        <div className="p-4 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400 animate-scale-in">
          {error}
        </div>
      )}

      {/* API Keys Section */}
      <Card className="mb-6 animate-slide-up">
        <CardHeader>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
            </svg>
            API Keys
          </h2>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-dark-200 mb-6">
            Configure API keys for data sources. Keys are encrypted and used for extraction.
          </p>

          {/* Google Places Card */}
          <div className={`border rounded-xl p-5 transition-all duration-200 ${googlePlacesKey ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-dark-500 bg-dark-850'}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-dark-700 border border-dark-500 flex items-center justify-center">
                  <svg className="w-5 h-5 text-dark-100" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="currentColor"/>
                  </svg>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-white">Google Places API</h3>
                    {googlePlacesKey ? (
                      <Badge variant="success">Active</Badge>
                    ) : (
                      <Badge variant="subtle">Not configured</Badge>
                    )}
                  </div>
                  <p className="text-xs text-dark-300 mt-1">
                    Search businesses via Google Places API (New)
                  </p>
                  {googlePlacesKey && (
                    <div className="flex items-center gap-4 mt-2 text-xs text-dark-300">
                      <span>Key: <code className="bg-dark-700 px-1.5 py-0.5 rounded font-mono text-dark-200">{googlePlacesKey.api_key_hint}</code></span>
                      {googlePlacesKey.last_verified_at && (
                        <span>Last verified: {new Date(googlePlacesKey.last_verified_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
              <div>
                {googlePlacesKey ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteKey(googlePlacesKey.id)}
                    icon={
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                      </svg>
                    }
                  >
                    Delete
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setShowAddForm(true)}
                    icon={
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                      </svg>
                    }
                  >
                    Add Key
                  </Button>
                )}
              </div>
            </div>

            {/* Add Key Form */}
            {showAddForm && !googlePlacesKey && (
              <div className="mt-5 pt-5 border-t border-dark-500 animate-slide-up">
                <Input
                  label="API Key"
                  type="password"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="Enter your Google Places API key"
                  icon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
                    </svg>
                  }
                />
                <p className="text-xs text-dark-300 mt-2">
                  Get your API key from{' '}
                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-400 hover:text-brand-300 font-medium"
                  >
                    Google Cloud Console
                  </a>
                </p>
                <div className="flex gap-2 mt-4">
                  <Button
                    size="sm"
                    loading={saving}
                    onClick={handleAddKey}
                    disabled={!newKey.trim()}
                  >
                    {saving ? 'Saving...' : 'Save Key'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { setShowAddForm(false); setNewKey(''); }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>

          {keys.length === 0 && !showAddForm && (
            <div className="text-center py-6 text-sm text-dark-300">
              No API keys configured. Add a key to start searching.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Account Section */}
      <Card className="animate-slide-up">
        <CardHeader>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <svg className="w-4 h-4 text-dark-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
            </svg>
            Account
          </h2>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-dark-300">
            Account management will be available in a future update.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
