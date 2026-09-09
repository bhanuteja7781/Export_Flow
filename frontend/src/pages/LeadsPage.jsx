import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import { 
  Search, 
  Download, 
  ShieldCheck, 
  Loader2, 
  CheckCircle2, 
  Pencil, 
  Mail, 
  MessageSquare, 
  Trash2,
  RotateCcw,
  Globe,
  Layers,
  BarChart3,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Building2,
  Store,
  Sliders,
  Check,
  Info,
  MapPin
} from 'lucide-react';
import { COUNTRIES, STATES_BY_COUNTRY, buildLocationQuery } from '../data/locations';

const BUYER_TYPE_META = {
  'diaspora_ethnic': { label: 'Diaspora & Ethnic', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)' },
  'wholesale_distributor': { label: 'Wholesale', color: '#818cf8', bg: 'rgba(129, 140, 248, 0.12)', border: 'rgba(129, 140, 248, 0.3)' },
  'furniture_lifestyle': { label: 'Furniture Stores', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.12)', border: 'rgba(6, 182, 212, 0.3)' },
  'home_decor_retailer': { label: 'Home Décor', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.3)' },
  'gift_specialty': { label: 'Gift Shops', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.3)' },
  'interior_design': { label: 'Interior Design', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.12)', border: 'rgba(168, 85, 247, 0.3)' },
  'wedding_event_decorator': { label: 'Wedding & Event', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.12)', border: 'rgba(236, 72, 153, 0.3)' },
  'hospitality_hotel': { label: 'Hotels & Hospitality', color: '#eab308', bg: 'rgba(234, 179, 8, 0.12)', border: 'rgba(234, 179, 8, 0.3)' },
  'event_party_rental': { label: 'Event Rental', color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)', border: 'rgba(249, 115, 22, 0.3)' }
};

const SOURCE_CHANNELS = [
  { id: 'wholesale', name: 'Wholesale Platforms', icon: '📦', defaultEnabled: true },
  { id: 'linkedin', name: 'LinkedIn Business', icon: '💼', defaultEnabled: true },
  { id: 'instagram', name: 'Instagram Boutiques', icon: '📸', defaultEnabled: true },
  { id: 'search_engine', name: 'Search Engines (Web)', icon: '🔍', defaultEnabled: true },
  { id: 'directory', name: 'Business Directories', icon: '🏢', defaultEnabled: true },
  { id: 'facebook', name: 'Facebook Showrooms', icon: '📘', defaultEnabled: true },
  { id: 'pinterest', name: 'Pinterest Visual Brands', icon: '📌', defaultEnabled: true },
  { id: 'youtube', name: 'YouTube Showrooms', icon: '🎬', defaultEnabled: true },
  { id: 'marketplace', name: 'Public Marketplaces', icon: '🛍️', defaultEnabled: true },
  { id: 'industry', name: 'Trade Associations', icon: '🏛️', defaultEnabled: true },
  { id: 'direct_website', name: 'Official Websites', icon: '🌐', defaultEnabled: true }
];

const getCategoryMeta = (category) => {
  if (BUYER_TYPE_META[category]) {
    return BUYER_TYPE_META[category];
  }
  const cat = (category || '').toLowerCase();
  if (cat.includes('diaspora') || cat.includes('ethnic') || cat.includes('india') || cat.includes('handicraft')) return BUYER_TYPE_META['diaspora_ethnic'];
  if (cat.includes('wholesale') || cat.includes('distributor') || cat.includes('import')) return BUYER_TYPE_META['wholesale_distributor'];
  if (cat.includes('furniture')) return BUYER_TYPE_META['furniture_lifestyle'];
  if (cat.includes('wedding') || cat.includes('event')) return BUYER_TYPE_META['wedding_event_decorator'];
  if (cat.includes('hotel') || cat.includes('hospitality') || cat.includes('restaurant')) return BUYER_TYPE_META['hospitality_hotel'];
  if (cat.includes('gift') || cat.includes('specialty')) return BUYER_TYPE_META['gift_specialty'];
  if (cat.includes('interior') || cat.includes('design') || cat.includes('staging')) return BUYER_TYPE_META['interior_design'];
  if (cat.includes('rental')) return BUYER_TYPE_META['event_party_rental'];
  return BUYER_TYPE_META['home_decor_retailer'];
};

const getSourceIcon = (sourceName = '') => {
  const s = sourceName.toLowerCase();
  if (s.includes('instagram')) return '📸';
  if (s.includes('linkedin')) return '💼';
  if (s.includes('facebook')) return '📘';
  if (s.includes('pinterest')) return '📌';
  if (s.includes('youtube')) return '🎬';
  if (s.includes('directory') || s.includes('yellow') || s.includes('manta')) return '🏢';
  if (s.includes('wholesale') || s.includes('faire')) return '📦';
  if (s.includes('market') || s.includes('etsy')) return '🛍️';
  if (s.includes('industry')) return '🏛️';
  if (s.includes('verified')) return '🌟';
  return '🌐';
};

const parseDateToTime = (dateStr, fallback = 0) => {
  if (!dateStr) return fallback;
  if (typeof dateStr === 'number') return dateStr;
  const s = String(dateStr).trim();

  if (s.includes('T') || s.includes('Z')) {
    const t = new Date(s).getTime();
    if (!isNaN(t)) return t;
  }

  if (s.includes('/')) {
    const parts = s.split('/');
    if (parts.length === 3) {
      const d = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10) - 1;
      const y = parseInt(parts[2], 10);
      const dt = new Date(y, m, d);
      if (!isNaN(dt.getTime())) return dt.getTime();
    }
  }

  if (s.includes('-')) {
    const parts = s.split('-');
    if (parts.length === 3) {
      const y = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10) - 1;
      const d = parseInt(parts[2], 10);
      const dt = new Date(y, m, d);
      if (!isNaN(dt.getTime())) return dt.getTime();
    }
  }

  const dt = new Date(s);
  return isNaN(dt.getTime()) ? fallback : dt.getTime();
};

export default function LeadsPage({
  leads = [],
  onSearch,
  onImportSelected,
  onValidate,
  onUpdateLead,
  onDeleteLead,
  onPurgeFailed,
  onRecheckAndClean,
  isPurging = false,
  isRechecking = false,
  onDownloadCSV,
  onClearLeads,
  isSearching,
  isValidating,
  settings = {},
  setActiveTab
}) {
  const [keyword, setKeyword] = useState(currentKeyword || settings?.searchKeyword || 'Metal Candle Holders');
  const [selectedCountry, setSelectedCountry] = useState('BOTH');
  const [selectedState, setSelectedState] = useState('All States/Provinces');
  const [selectedCity, setSelectedCity] = useState('All Cities');
  const [customCity, setCustomCity] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  
  const [enabledSources, setEnabledSources] = useState(
    SOURCE_CHANNELS.reduce((acc, s) => ({ ...acc, [s.id]: true }), {})
  );
  const [sourceAnalyticsData, setSourceAnalyticsData] = useState([]);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  const [editingLead, setEditingLead] = useState(null);
  const [viewingReply, setViewingReply] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [replyFilter, setReplyFilter] = useState('all');
  const [lastSearchResult, setLastSearchResult] = useState(null);

  const currentStates = STATES_BY_COUNTRY[selectedCountry] || [];
  const currentStateObj = currentStates.find(s => s.name === selectedState) || currentStates[0];
  const currentCities = currentStateObj ? currentStateObj.cities : [];

  const handleCountryChange = (countryId) => {
    setSelectedCountry(countryId);
    const stateList = STATES_BY_COUNTRY[countryId] || [];
    if (stateList.length > 0) {
      const firstState = stateList[0].name;
      setSelectedState(firstState);
      setSelectedCity(stateList[0].cities[0] || 'All Cities');
    } else {
      setSelectedState('');
      setSelectedCity('');
    }
    setCustomCity('');
  };

  const handleStateChange = (stateName) => {
    setSelectedState(stateName);
    const stateList = STATES_BY_COUNTRY[selectedCountry] || [];
    const stateObj = stateList.find(s => s.name === stateName);
    if (stateObj && stateObj.cities.length > 0) {
      setSelectedCity(stateObj.cities[0]);
    } else {
      setSelectedCity('All Cities');
    }
    setCustomCity('');
  };

  const contactedCount = leads.filter(l => Boolean(l.last_contacted_at)).length;
  const repliedCount = leads.filter(l => l.reply_status === 'replied' || (l.responses && l.responses.toLowerCase().includes('replied') && !l.responses.toLowerCase().includes('awaiting'))).length;
  const autoReplyCount = leads.filter(l => l.reply_status === 'auto_reply' || (l.responses && (l.responses.toLowerCase().includes('automated') || l.responses.toLowerCase().includes('auto-reply')))).length;

  // Fetch live Source Performance Analytics
  const fetchAnalytics = async () => {
    setIsLoadingAnalytics(true);
    try {
      const res = await fetch('/api/discovery/analytics');
      if (res.ok) {
        const data = await res.json();
        setSourceAnalyticsData(data.analytics || []);
      }
    } catch (e) {
      console.warn('Analytics fetch note:', e);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [leads.length]);

  const toggleSource = (sourceId) => {
    setEnabledSources(prev => ({
      ...prev,
      [sourceId]: !prev[sourceId]
    }));
  };

  const selectAllSources = (val) => {
    const updated = {};
    SOURCE_CHANNELS.forEach(s => {
      updated[s.id] = val;
    });
    setEnabledSources(updated);
  };

  // Discover candidate buyers across all sources and add directly to directory
  const handleSearchSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!keyword.trim()) return;

    const locQuery = buildLocationQuery(selectedCountry, selectedState, selectedCity, customCity);
    const activeList = Object.keys(enabledSources).filter(k => enabledSources[k]);

    const result = await onSearch({
      keyword: keyword.trim(),
      location: locQuery,
      country: selectedCountry === 'BOTH' ? 'United States, Canada' : (selectedCountry === 'USA' ? 'United States' : 'Canada'),
      state: selectedState.startsWith('All') ? '' : selectedState.replace(' (USA)', '').replace(' (Canada)', ''),
      city: customCity.trim() || (selectedCity.startsWith('All') ? '' : selectedCity),
      buyer_type: 'all',
      sources: activeList.length > 0 ? activeList : null,
      limit: maxResults,
      preview: false
    });

    if (result) {
      setLastSearchResult({ ...result, searchedLocation: locQuery, searchedKeyword: keyword });
      fetchAnalytics();
    }
  };

  const handleEdit = (lead) => {
    setEditingLead({ ...lead });
  };

  const handleSaveEdit = () => {
    if (editingLead) {
      onUpdateLead(editingLead.id, editingLead);
      setEditingLead(null);
    }
  };

  const filteredLeads = leads
    .filter(lead => {
      const matchSearch =
        searchTerm === '' ||
        (lead.company_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.city || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.state || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.country || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.keyword || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.primary_source || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.responses || '').toLowerCase().includes(searchTerm.toLowerCase());

      const isContacted = Boolean(lead.last_contacted_at);
      const isAutoReply = lead.reply_status === 'auto_reply' || (lead.responses && (lead.responses.toLowerCase().includes('automated') || lead.responses.toLowerCase().includes('auto-reply')));
      const isReplied = lead.reply_status === 'replied' || (lead.responses && lead.responses.toLowerCase().includes('replied') && !lead.responses.toLowerCase().includes('awaiting'));

      const matchReply =
        replyFilter === 'all' ||
        (replyFilter === 'replied' && isReplied) ||
        (replyFilter === 'auto_reply' && isAutoReply) ||
        (replyFilter === 'uncontacted' && !isContacted) ||
        (replyFilter === 'unreplied' && isContacted && !isReplied && !isAutoReply);

      return matchSearch && matchReply;
    })
    .sort((a, b) => {
      const aSent = Boolean(a.last_contacted_at);
      const bSent = Boolean(b.last_contacted_at);
      if (!aSent && bSent) return -1;
      if (aSent && !bSent) return 1;

      const timeA = parseDateToTime(a.discovered_at || a.last_contacted_at || a.date, 0);
      const timeB = parseDateToTime(b.discovered_at || b.last_contacted_at || b.date, 0);
      return timeB - timeA;
    });

  const activeSourceCount = Object.values(enabledSources).filter(Boolean).length;

  return (
    <div className="page-container">
      <Header
        breadcrumb="SaaS Workspace / Discovery"
        title="Public Buyer Discovery"
        subtitle="Discover and verify commercial buyers, wholesale importers, and lifestyle boutiques across America & Canada."
      />

      {/* 1. Public Buyer Discovery Search Card */}
      <div className="app-card" style={{ marginBottom: '24px', padding: '24px 28px' }}>
        <form onSubmit={handleSearchSubmit}>
          
          {/* Single Line: Keywords, Countries, States, Cities, No. of Buyers, Discover */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, minmax(0, 1fr)) auto',
            gap: '12px',
            alignItems: 'flex-end'
          }}>
            {/* 1. Keywords */}
            <div className="form-group" style={{ margin: 0, minWidth: 0 }}>
              <label className="form-label" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', display: 'block', whiteSpace: 'nowrap' }}>
                Keywords
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. candles, wholesale"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                style={{ height: '42px', fontSize: '13px', width: '100%' }}
              />
            </div>

            {/* 2. Countries */}
            <div className="form-group" style={{ margin: 0, minWidth: 0 }}>
              <label className="form-label" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', display: 'block', whiteSpace: 'nowrap' }}>
                Countries
              </label>
              <select
                className="input-field"
                value={selectedCountry}
                onChange={(e) => handleCountryChange(e.target.value)}
                style={{ height: '42px', fontSize: '13px', width: '100%', background: 'var(--card-bg, #0f172a)', cursor: 'pointer' }}
              >
                {COUNTRIES.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.flag} {c.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 3. States */}
            <div className="form-group" style={{ margin: 0, minWidth: 0 }}>
              <label className="form-label" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', display: 'block', whiteSpace: 'nowrap' }}>
                States
              </label>
              <select
                className="input-field"
                value={selectedState}
                onChange={(e) => handleStateChange(e.target.value)}
                style={{ height: '42px', fontSize: '13px', width: '100%', background: 'var(--card-bg, #0f172a)', cursor: 'pointer' }}
              >
                {currentStates.map(st => (
                  <option key={st.code || st.name} value={st.name}>
                    {st.name} {st.code && !st.code.startsWith('ALL') ? `(${st.code})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* 4. Cities */}
            <div className="form-group" style={{ margin: 0, minWidth: 0 }}>
              <label className="form-label" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', display: 'block', whiteSpace: 'nowrap' }}>
                Cities
              </label>
              <select
                className="input-field"
                value={selectedCity}
                onChange={(e) => {
                  setSelectedCity(e.target.value);
                  if (e.target.value !== '__custom__') {
                    setCustomCity('');
                  }
                }}
                style={{ height: '42px', fontSize: '13px', width: '100%', background: 'var(--card-bg, #0f172a)', cursor: 'pointer' }}
              >
                {currentCities.map(city => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
                <option value="__custom__">✏️ Other / Type Custom City...</option>
              </select>
            </div>

            {/* 5. No. of Buyers */}
            <div className="form-group" style={{ margin: 0, minWidth: 0 }}>
              <label className="form-label" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px', display: 'block', whiteSpace: 'nowrap' }}>
                No. of Buyers
              </label>
              <select
                className="input-field"
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                style={{ height: '42px', fontSize: '13px', width: '100%', background: 'var(--card-bg, #0f172a)', cursor: 'pointer' }}
              >
                <option value={5}>5 Buyers</option>
                <option value={10}>10 Buyers</option>
                <option value={15}>15 Buyers</option>
                <option value={20}>20 Buyers</option>
              </select>
            </div>

            {/* Discover Button */}
            <div style={{ margin: 0 }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSearching}
                style={{
                  height: '42px',
                  fontSize: '13.5px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  borderRadius: '8px',
                  background: '#2563eb',
                  borderColor: '#2563eb',
                  padding: '0 22px',
                  whiteSpace: 'nowrap'
                }}
              >
                {isSearching ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
                <span>{isSearching ? 'Discovering...' : 'Discover'}</span>
              </button>
            </div>
          </div>

          {/* Optional Custom City text input when user picks "Other / Type Custom City..." */}
          {selectedCity === '__custom__' && (
            <div style={{ marginTop: '14px', maxWidth: '360px' }}>
              <label className="form-label" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', display: 'block' }}>
                Custom City Name in {selectedState}:
              </label>
              <input
                type="text"
                className="input-field"
                placeholder={`e.g. city or town in ${selectedState}`}
                value={customCity}
                onChange={(e) => setCustomCity(e.target.value)}
                style={{ height: '40px', fontSize: '13px' }}
                autoFocus
              />
            </div>
          )}

        </form>
      </div>

      {/* 2. Buyers Directory Table */}
      <div className="app-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 className="card-heading" style={{ margin: 0 }}>Buyers Directory ({leads.length})</h2>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* 1. Verify MX */}
            {onValidate && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onValidate}
                disabled={isValidating || leads.length === 0}
                title="Verify deliverability via DNS MX lookup"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                {isValidating ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />}
                <span>{isValidating ? 'Verifying MX...' : 'Verify MX'}</span>
              </button>
            )}

            {/* 2. Purge Bounced */}
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onRecheckAndClean || onPurgeFailed}
              disabled={isPurging || isRechecking || leads.length === 0}
              title="Scan mailbox for bounce notifications and purge invalid buyers"
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {(isPurging || isRechecking) ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
              <span>{(isPurging || isRechecking) ? 'Rechecking...' : 'Purge Bounced'}</span>
            </button>

            {/* 3. Export CSV */}
            {onDownloadCSV && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onDownloadCSV}
                disabled={leads.length === 0}
                title="Export buyers directory to CSV spreadsheet"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Download size={13} />
                <span>Export CSV</span>
              </button>
            )}

            {/* 4. Compose Campaign */}
            {setActiveTab && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setActiveTab('campaigns')}
                disabled={leads.length === 0}
                title="Compose outreach campaign for active buyers"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Mail size={13} />
                <span>Compose Campaign &rarr;</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter Controls */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '180px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-dim)' }} />
            <input
              type="text"
              className="input-field"
              placeholder="Search by buyer name, company, email, or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '32px' }}
            />
          </div>

          <select
            className="input-field"
            value={replyFilter}
            onChange={(e) => setReplyFilter(e.target.value)}
            style={{ width: '190px' }}
          >
            <option value="all">All Status ({leads.length})</option>
            <option value="replied">Replied ({repliedCount})</option>
            <option value="auto_reply">Auto-Reply ({autoReplyCount})</option>
            <option value="unreplied">Sent — Awaiting Reply ({Math.max(0, contactedCount - repliedCount - autoReplyCount)})</option>
            <option value="uncontacted">Uncontacted ({Math.max(0, leads.length - contactedCount)})</option>
          </select>
        </div>

        {/* Leads Table */}
        <div className="app-table-container">
          <table className="app-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '32%', padding: '10px 12px' }}>Buyer & Company</th>
                <th style={{ width: '28%', padding: '10px 8px' }}>Email Address</th>
                <th style={{ width: '22%', padding: '10px 8px' }}>Category & Location</th>
                <th style={{ width: '18%', padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
                    {leads.length === 0 ? (
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                          Directory is empty
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          Click <strong>Discover</strong> above to start discovering B2B buyers across America & Canada.
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                          No matching buyers
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          Try clearing filters or changing search keywords.
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                filteredLeads.map((lead) => {
                  const isAutoReply = lead.reply_status === 'auto_reply' || (lead.responses && (lead.responses.toLowerCase().includes('automated') || lead.responses.toLowerCase().includes('auto-reply')));
                  const isReplied = lead.reply_status === 'replied' || (lead.responses && lead.responses.toLowerCase().includes('replied') && !lead.responses.toLowerCase().includes('awaiting'));
                  const isContacted = Boolean(lead.last_contacted_at);
                  const catMeta = getCategoryMeta(lead.category);

                  return (
                    <tr key={lead.id || lead.email}>
                      {/* Buyer & Company */}
                      <td style={{ padding: '8px 12px', maxWidth: '220px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={lead.company_name || lead.buyer_name}>
                            {lead.company_name || lead.buyer_name || 'Commercial Buyer'}
                          </span>
                          {lead.website && (
                            <a
                              href={lead.website}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#64748b', display: 'inline-flex', alignItems: 'center' }}
                              title={lead.website}
                            >
                              <ExternalLink size={11} />
                            </a>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {lead.buyer_name && lead.buyer_name !== 'Purchasing Team' && lead.buyer_name !== 'Buyer' && lead.buyer_name !== lead.company_name
                            ? lead.buyer_name
                            : (lead.city && lead.state ? `${lead.city}, ${lead.state}` : (lead.country || 'USA'))}
                        </div>
                      </td>

                      {/* Email Address & MX */}
                      <td style={{ padding: '8px 8px', maxWidth: '200px' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#93c5fd', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={lead.email}>
                          {lead.email}
                        </span>
                        <div>
                          {lead.reply_status === 'bounced' ? (
                            <span style={{ fontSize: '9.5px', color: '#f87171', fontWeight: 600 }}>Bounced ⚠️</span>
                          ) : (lead.validation_status === 'valid' || lead.is_mx_verified === true) ? (
                            <span style={{ fontSize: '9.5px', color: '#4ade80', fontWeight: 500 }}>MX Verified ✓</span>
                          ) : lead.validation_status === 'invalid' ? (
                            <span style={{ fontSize: '9.5px', color: '#f87171', fontWeight: 600 }}>Undeliverable ✗</span>
                          ) : lead.validation_status === 'risky' ? (
                            <span style={{ fontSize: '9.5px', color: '#fbbf24', fontWeight: 500 }}>MX Risky ⚠️</span>
                          ) : (
                            <span style={{ fontSize: '9.5px', color: '#94a3b8', fontWeight: 500 }}>⚪ Unverified</span>
                          )}
                        </div>
                      </td>

                      {/* Category & Location */}
                      <td style={{ padding: '8px 8px' }}>
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 500,
                          color: catMeta.color,
                          background: catMeta.bg,
                          border: `1px solid ${catMeta.border}`,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          display: 'inline-block',
                          marginBottom: '2px'
                        }}>
                          {catMeta.label}
                        </span>
                        <div style={{ fontSize: '10.5px', color: 'var(--text-dim)' }}>
                          📍 {lead.city ? `${lead.city}, ${lead.state || lead.country || ''}` : (lead.state || lead.country || 'USA')}
                        </div>
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '5px', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {isReplied ? (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => setViewingReply(lead)}
                              style={{ padding: '3px 7px', fontSize: '10px', color: '#4ade80', borderColor: 'rgba(74, 222, 128, 0.4)', background: 'rgba(74, 222, 128, 0.1)' }}
                            >
                              <span>Replied ✓</span>
                            </button>
                          ) : isAutoReply ? (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => setViewingReply(lead)}
                              style={{ padding: '3px 7px', fontSize: '10px', color: '#fbbf24', borderColor: 'rgba(251, 191, 36, 0.4)', background: 'rgba(251, 191, 36, 0.15)' }}
                              title="View Automated Reply"
                            >
                              <span>Auto-Reply 🤖</span>
                            </button>
                          ) : isContacted ? (
                            <span style={{ fontSize: '10px', color: '#60a5fa', background: 'rgba(59, 130, 246, 0.12)', padding: '2px 5px', borderRadius: '4px' }}>
                              Sent ✓
                            </span>
                          ) : (
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              onClick={() => setActiveTab && setActiveTab('campaigns')}
                              style={{ padding: '3px 7px', fontSize: '10px' }}
                            >
                              <Mail size={11} />
                              <span>Reach Out</span>
                            </button>
                          )}

                          {/* Edit Buyer */}
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => setEditingLead({ ...lead })}
                            style={{ padding: '3px 5px' }}
                            title="Edit Buyer Details"
                          >
                            <Pencil size={11} />
                          </button>

                          {/* Delete */}
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              if (window.confirm(`Delete "${lead.company_name || lead.email}" and permanently blacklist from future discovery?`)) {
                                if (onDeleteLead) {
                                  onDeleteLead(lead.id || lead.email);
                                }
                              }
                            }}
                            style={{ padding: '3px 5px', color: '#f87171' }}
                            title="Delete Buyer & Blacklist Domain"
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Buyer Modal */}
      {editingLead && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#0f172a',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '480px',
            padding: '20px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
          }}>
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px' }}>
              Edit Buyer Information
            </h3>

            <form onSubmit={handleSaveEdit}>
              <div className="form-group">
                <label className="form-label">Buyer Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingLead.buyer_name || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, buyer_name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Company Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingLead.company_name || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, company_name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="input-field"
                  value={editingLead.email || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, email: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Website URL</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingLead.website || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, website: e.target.value })}
                  placeholder="https://example.com"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Intern's Feedback / Assessment</label>
                <textarea
                  rows={2}
                  className="input-field"
                  value={editingLead.intern_feedback || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, intern_feedback: e.target.value })}
                  placeholder="Notes, qualification feedback, product suitability..."
                  style={{ resize: 'vertical' }}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Follow-ups Action Plan</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingLead.follow_ups || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, follow_ups: e.target.value })}
                  placeholder="e.g. Send MOQ matrix & follow up"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Country / Region</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingLead.country || ''}
                  onChange={(e) => setEditingLead({ ...editingLead, country: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setEditingLead(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. Reply Snippet Inspection Modal */}
      {viewingReply && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: '#0f172a',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '520px',
            padding: '20px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  Inbound Reply from {viewingReply.buyer_name || viewingReply.company_name}
                </h3>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {viewingReply.email} &bull; {viewingReply.company_name} ({viewingReply.country || 'USA'})
                </div>
              </div>

              <button
                type="button"
                onClick={() => setViewingReply(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{
              background: '#070b14',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              padding: '12px 14px',
              fontSize: '12px',
              lineHeight: '1.6',
              color: '#cbd5e1',
              marginBottom: '16px',
              whiteSpace: 'pre-wrap'
            }}>
              {viewingReply.reply_snippet || 'Buyer expressed interest in your catalog collection.'}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setViewingReply(null)}
              >
                Close
              </button>
              {setActiveTab && (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => {
                    setViewingReply(null);
                    setActiveTab('inbox');
                  }}
                >
                  Open Inbox &rarr;
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
