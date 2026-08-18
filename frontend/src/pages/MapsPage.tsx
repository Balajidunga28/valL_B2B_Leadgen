/**
 * url: /frontend/src/pages/MapsPage.tsx
 * About:
 *   Maps page for ValLG. Displays lead locations on an OpenStreetMap/Leaflet
 *   map with dark tiles. Shows markers for all leads with valid coordinates.
 *   Clicking a marker shows business info popup with directions link.
 *   Uses the unified /api/leads endpoint for real scored/enriched data.
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { Card, PageHeader, Skeleton, EmptyState } from '../components/ui';
import type { Lead } from '../types';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const DARK_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const DARK_TILE_ATTR = '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>';

function createMarkerIcon(): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="
      width: 14px; height: 14px;
      background: #5b5bd6;
      border: 2px solid #818cf8;
      border-radius: 50%;
      box-shadow: 0 0 8px rgba(91,91,214,0.6);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  });
}

function buildPopupContent(lead: Lead): string {
  const name = lead.name || 'Unknown';
  const address = [lead.city, lead.state].filter(Boolean).join(', ') || 'No location';
  const phone = lead.phone || '';
  const industry = lead.industry || '';
  const rating = lead.rating != null ? `★ ${lead.rating}` : '';
  const score = lead.total_score != null ? `Score: ${lead.total_score.toFixed(1)}` : '';
  const source = lead.source || '';

  const directionsUrl = lead.latitude && lead.longitude
    ? `https://www.google.com/maps/dir/?api=1&destination=${lead.latitude},${lead.longitude}`
    : '';

  return `
    <div style="font-family:Inter,system-ui,sans-serif;min-width:220px;max-width:300px;background:#08080d;color:#e0e0e8;border-radius:8px;padding:0;overflow:hidden;">
      <div style="padding:12px 14px 8px;border-bottom:1px solid #2a2a3a;">
        <div style="font-size:14px;font-weight:700;color:#f0f0f8;margin-bottom:2px;">${name}</div>
        ${industry ? `<div style="font-size:11px;color:#818cf8;margin-bottom:4px;">${industry}</div>` : ''}
        ${rating ? `<div style="font-size:12px;color:#f59e0b;margin-bottom:2px;">${rating}</div>` : ''}
        ${score ? `<div style="font-size:11px;color:#34d399;margin-bottom:2px;">${score}</div>` : ''}
      </div>
      <div style="padding:8px 14px;font-size:12px;line-height:1.6;">
        <div style="color:#b0b0c0;">📍 ${address}</div>
        ${phone ? `<div style="color:#b0b0c0;">📞 ${phone}</div>` : ''}
        ${lead.website ? `<div style="color:#b0b0c0;">🌐 <a href="${lead.website}" target="_blank" style="color:#818cf8;">${(() => { try { return new URL(lead.website).hostname; } catch { return lead.website; } })()}</a></div>` : ''}
        <div style="color:#6b7280;font-size:10px;margin-top:4px;">Source: ${source}</div>
      </div>
      <div style="padding:6px 14px 10px;display:flex;gap:8px;border-top:1px solid #2a2a3a;">
        ${directionsUrl ? `<a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:#5b5bd6;color:white;border-radius:5px;font-size:11px;font-weight:600;text-decoration:none;">🧭 Directions</a>` : ''}
      </div>
    </div>
  `;
}

export default function MapsPage() {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ total: 0, withCoords: 0, withoutCoords: 0 });

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const allLeads: Lead[] = [];
      let offset = 0;
      const limit = 500;
      let hasMore = true;

      while (hasMore) {
        const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
        const data = await apiClient.get<Lead[]>(`/leads?${params}`);
        allLeads.push(...data);
        if (data.length < limit) hasMore = false;
        else offset += limit;
      }

      const withCoords = allLeads.filter(
        (l) => l.latitude != null && l.longitude != null && !isNaN(l.latitude) && !isNaN(l.longitude)
      );
      setLeads(allLeads);
      setStats({ total: allLeads.length, withCoords: withCoords.length, withoutCoords: allLeads.length - withCoords.length });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  const initMap = useCallback(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [20.5937, 78.9629],
      zoom: 5,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer(DARK_TILE_URL, {
      attribution: DARK_TILE_ATTR,
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    mapInstanceRef.current = map;
    markersLayerRef.current = L.layerGroup().addTo(map);
  }, []);

  useEffect(() => {
    initMap();
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [initMap]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();

    const withCoords = leads.filter(
      (l) => l.latitude != null && l.longitude != null && !isNaN(l.latitude) && !isNaN(l.longitude)
    );

    if (withCoords.length === 0) {
      map.setView([20.5937, 78.9629], 5);
      return;
    }

    const bounds = L.latLngBounds([]);
    const icon = createMarkerIcon();

    withCoords.forEach((lead) => {
      const latlng = L.latLng(lead.latitude!, lead.longitude!);
      bounds.extend(latlng);

      const marker = L.marker(latlng, { icon });
      marker.bindPopup(buildPopupContent(lead), {
        className: 'dark-popup',
        maxWidth: 320,
        closeButton: true,
      });
      markersLayer.addLayer(marker);
    });

    if (withCoords.length <= 5) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    } else {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [leads]);

  return (
    <div>
      <PageHeader
        title="Lead Map"
        description={`${stats.withCoords} leads with locations out of ${stats.total} total`}
        actions={
          <div className="flex gap-2">
            <Link
              to="/results"
              className="inline-flex items-center gap-2 px-4 py-2 bg-dark-700 text-dark-100 text-sm font-medium rounded-lg border border-dark-500 hover:border-brand-500/50 hover:bg-brand-600/10 transition-all duration-150"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v.375" />
              </svg>
              View Results
            </Link>
          </div>
        }
      />

      {error && (
        <div className="p-4 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stats bar */}
      {!loading && stats.total > 0 && (
        <div className="mb-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2 text-dark-200">
            <div className="w-3 h-3 rounded-full bg-brand-500"></div>
            <span>{stats.withCoords} with coordinates</span>
          </div>
          {stats.withoutCoords > 0 && (
            <div className="flex items-center gap-2 text-dark-300">
              <div className="w-3 h-3 rounded-full bg-dark-500"></div>
              <span>{stats.withoutCoords} without coordinates</span>
            </div>
          )}
        </div>
      )}

      {/* Map container */}
      {loading ? (
        <Card className="overflow-hidden">
          <Skeleton className="h-[600px]" />
        </Card>
      ) : stats.withCoords === 0 ? (
        <Card>
          <EmptyState
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503-11.953a7.5 7.5 0 0 0-7.506 0M12 2.25l6.75 3-6.75 3-6.75-3 6.75-3Z" />
              </svg>
            }
            title="No leads with coordinates"
            description="Run a search to extract leads with geographic data. Google Maps and OpenStreetMap sources provide coordinates."
            action={
              <Link to="/search" className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-500 transition-colors">
                Start a search
              </Link>
            }
          />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div
            ref={mapRef}
            style={{ height: '600px', width: '100%', background: '#0a0a12' }}
          />
        </Card>
      )}
    </div>
  );
}
