import React, { useState } from 'react';
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
  RotateCcw
} from 'lucide-react';

const BUYER_TYPE_META = {
  'home_decor_retailer': { label: 'Home Décor', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.3)' },
  'wedding_event_decorator': { label: 'Wedding & Event', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.12)', border: 'rgba(236, 72, 153, 0.3)' },
  'hospitality_hotel': { label: 'Hotels & Hospitality', color: '#eab308', bg: 'rgba(234, 179, 8, 0.12)', border: 'rgba(234, 179, 8, 0.3)' },
  'gift_specialty': { label: 'Gift Shops', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.3)' },
  'interior_design': { label: 'Interior Design', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.12)', border: 'rgba(168, 85, 247, 0.3)' },
  'event_party_rental': { label: 'Event Rental', color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)', border: 'rgba(249, 115, 22, 0.3)' },
  'furniture_lifestyle': { label: 'Furniture Stores', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.12)', border: 'rgba(6, 182, 212, 0.3)' },
  'wholesale_distributor': { label: 'Wholesale', color: '#818cf8', bg: 'rgba(129, 140, 248, 0.12)', border: 'rgba(129, 140, 248, 0.3)' }
};

const getCategoryMeta = (category) => {
  if (BUYER_TYPE_META[category]) {
    return BUYER_TYPE_META[category];
  }
  const cat = (category || '').toLowerCase();
  if (cat.includes('wedding') || cat.includes('event')) return BUYER_TYPE_META['wedding_event_decorator'];
  if (cat.includes('hotel') || cat.includes('hospitality') || cat.includes('restaurant')) return BUYER_TYPE_META['hospitality_hotel'];
  if (cat.includes('gift') || cat.includes('specialty')) return BUYER_TYPE_META['gift_specialty'];
  if (cat.includes('interior') || cat.includes('design') || cat.includes('staging')) return BUYER_TYPE_META['interior_design'];
  if (cat.includes('rental')) return BUYER_TYPE_META['event_party_rental'];
  if (cat.includes('furniture')) return BUYER_TYPE_META['furniture_lifestyle'];
  if (cat.includes('wholesale') || cat.includes('distributor') || cat.includes('import')) return BUYER_TYPE_META['wholesale_distributor'];
  return BUYER_TYPE_META['home_decor_retailer'];
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
  currentKeyword,
  settings = {},
  setActiveTab
}) {
  const [keyword, setKeyword] = useState(currentKeyword || 'Metal Candle Holders');
  const [targetBuyerType, setTargetBuyerType] = useState('all');
  const [country, setCountry] = useState('America & Canada');
  const [maxResults, setMaxResults] = useState(10);
  const [editingLead, setEditingLead] = useState(null);
  const [viewingReply, setViewingReply] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [replyFilter, setReplyFilter] = useState('all');
  const [lastSearchResult, setLastSearchResult] = useState(null);

  const contactedCount = leads.filter(l => Boolean(l.last_contacted_at)).length;
  const repliedCount = leads.filter(l => l.reply_status === 'replied' || (l.responses && l.responses.toLowerCase().includes('replied') && !l.responses.toLowerCase().includes('awaiting'))).length;
  const autoReplyCount = leads.filter(l => l.reply_status === 'auto_reply' || (l.responses && (l.responses.toLowerCase().includes('automated') || l.responses.toLowerCase().includes('auto-reply')))).length;

  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    const result = await onSearch({
      keyword,
      country,
      buyer_type: targetBuyerType,
      source: 'all',
      limit: maxResults
    });

    if (result) {
      setLastSearchResult({ ...result, searchedCountry: country });
    }
  };

  const handleSaveEdit = (e) => {
    e.preventDefault();
    if (!editingLead) return;

    if (onUpdateLead) {
      onUpdateLead(editingLead);
    }
    setEditingLead(null);
  };

  const filteredLeads = [...leads]
    .filter((lead) => {
      const matchSearch =
        !searchTerm ||
        (lead.buyer_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.company_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (lead.country || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
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
      const timeA = parseDateToTime(a.discovered_at || a.last_contacted_at || a.date, 0);
      const timeB = parseDateToTime(b.discovered_at || b.last_contacted_at || b.date, 0);
      return timeB - timeA;
    });

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / BUYERS"
        title="Buyers Directory"
        subtitle="Discover and manage verified B2B buyers across America & Canada."
      />

      {/* 1. Clean Search Card */}
      <div className="app-card" style={{ marginBottom: '20px', padding: '18px 20px' }}>
        <form onSubmit={handleSearchSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px', alignItems: 'flex-end' }}>
            
            {/* Product Keyword */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Product Keyword</label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. Metal Candle Holders"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
            </div>

            {/* Target Buyer Type */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Buyer Type</label>
              <select
                className="input-field"
                value={targetBuyerType}
                onChange={(e) => setTargetBuyerType(e.target.value)}
              >
                <option value="all">All Buyer Types</option>
                <option value="home_decor_retailer">Home Décor Retailers</option>
                <option value="wedding_event_decorator">Wedding & Event Decorators</option>
                <option value="hospitality_hotel">Hotels & Hospitality</option>
                <option value="gift_specialty">Gift & Specialty Stores</option>
                <option value="interior_design">Interior Design Firms</option>
                <option value="event_party_rental">Event & Party Rentals</option>
                <option value="furniture_lifestyle">Furniture Stores</option>
                <option value="wholesale_distributor">Wholesalers & Distributors</option>
              </select>
            </div>

            {/* Target Market / Country Selection */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Search Country</label>
              <select
                className="input-field"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              >
                <option value="America & Canada">🌎 Both USA & Canada</option>
                <option value="United States">🇺🇸 United States (USA)</option>
                <option value="Canada">🇨🇦 Canada</option>
              </select>
            </div>

            {/* Results Limit */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Results Limit</label>
              <select
                className="input-field"
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
              >
                <option value={5}>5 Buyers</option>
                <option value={10}>10 Buyers</option>
                <option value={15}>15 Buyers</option>
                <option value={20}>20 Buyers</option>
              </select>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSearching}
                style={{ width: '100%', justifyContent: 'center', height: '38px' }}
              >
                {isSearching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                <span>{isSearching ? 'Searching...' : 'Search Buyers'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Search Result Summary Banner */}
      {lastSearchResult && (() => {
        const addedCount = lastSearchResult.newly_added || lastSearchResult.newlyAdded || 0;
        const searched = lastSearchResult.searchedCountry || country;
        const countryLabel = searched === 'Canada' 
          ? 'Canada' 
          : searched === 'United States' 
          ? 'the United States' 
          : 'Both USA & Canada';

        return (
          <div style={{
            padding: '10px 14px',
            background: addedCount > 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(59, 130, 246, 0.1)',
            border: addedCount > 0 ? '1px solid rgba(34, 197, 94, 0.4)' : '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '6px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={16} color={addedCount > 0 ? 'var(--success)' : '#60a5fa'} />
              <span style={{ fontSize: '12px', color: 'var(--text-main)' }}>
                {addedCount > 0 
                  ? <>Added <strong>{addedCount} new buyers</strong> across {countryLabel}.</>
                  : <>Directory is up to date with matching buyers across {countryLabel}.</>
                }
              </span>
            </div>

            <button
              type="button"
              onClick={() => setLastSearchResult(null)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '12px' }}
            >
              ✕
            </button>
          </div>
        );
      })()}

      {/* 2. Buyers Directory Table */}
      <div className="app-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 className="card-heading" style={{ margin: 0 }}>Buyers Directory ({leads.length})</h2>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {onValidate && leads.length > 0 && (
              <button className="btn btn-secondary btn-sm" onClick={onValidate} disabled={isValidating} title="Verify DNS MX mail servers">
                {isValidating ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />}
                <span>{isValidating ? 'Verifying...' : 'Verify MX'}</span>
              </button>
            )}

            {(onRecheckAndClean || onPurgeFailed) && leads.length > 0 && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onRecheckAndClean || onPurgeFailed}
                disabled={isPurging || isRechecking}
                title="Scan mailbox for bounce notifications (Address not found) and purge invalid buyers from database and reports"
              >
                {(isPurging || isRechecking) ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
                <span>{(isPurging || isRechecking) ? 'Rechecking & Purging...' : 'Purge Bounced'}</span>
              </button>
            )}

            {onDownloadCSV && leads.length > 0 && (
              <button className="btn btn-secondary btn-sm" onClick={onDownloadCSV}>
                <Download size={13} />
                <span>Export CSV</span>
              </button>
            )}

            {setActiveTab && leads.length > 0 && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setActiveTab('campaigns')}
              >
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
              placeholder="Search by name, company, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '32px' }}
            />
          </div>

          <select
            className="input-field"
            value={replyFilter}
            onChange={(e) => setReplyFilter(e.target.value)}
            style={{ width: '210px' }}
          >
            <option value="all">All Status ({leads.length})</option>
            <option value="replied">Replied ({repliedCount})</option>
            <option value="auto_reply">Automated Reply ({autoReplyCount})</option>
            <option value="unreplied">Sent — Awaiting Reply ({Math.max(0, contactedCount - repliedCount - autoReplyCount)})</option>
            <option value="uncontacted">Uncontacted ({Math.max(0, leads.length - contactedCount)})</option>
          </select>
        </div>

        {/* Leads Table */}
        <div className="app-table-container">
          <table className="app-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '22%', padding: '10px 12px' }}>Buyer & Company</th>
                <th style={{ width: '22%', padding: '10px 12px' }}>Email Address</th>
                <th style={{ width: '8%', padding: '10px 8px' }}>Region</th>
                <th style={{ width: '14%', padding: '10px 8px' }}>Buyer Category</th>
                <th style={{ width: '10%', padding: '10px 8px' }}>Deliverability</th>
                <th style={{ width: '12%', padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px 20px', color: 'var(--text-muted)' }}>
                    {leads.length === 0 ? (
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                          Database is empty
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          Click <strong>Search Buyers</strong> above to discover B2B buyers across America & Canada.
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
                      <td style={{ padding: '8px 12px', maxWidth: '170px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={lead.company_name || lead.buyer_name}>
                          {lead.company_name || lead.buyer_name || 'Commercial Buyer'}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={lead.buyer_name && lead.buyer_name !== 'Purchasing Team' && lead.buyer_name !== 'Procurement Buyer' && lead.buyer_name !== 'Buyer' ? lead.buyer_name : ''}>
                          {lead.buyer_name && lead.buyer_name !== 'Purchasing Team' && lead.buyer_name !== 'Procurement Buyer' && lead.buyer_name !== 'Buyer' && lead.buyer_name !== lead.company_name ? lead.buyer_name : (lead.country || 'United States')}
                        </div>
                      </td>

                      <td style={{ padding: '8px 12px', maxWidth: '180px' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#93c5fd', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={lead.email}>
                          {lead.email}
                        </span>
                      </td>

                      <td style={{ padding: '8px 8px', fontSize: '11px', color: 'var(--text-main)' }}>
                        {lead.country || 'USA'}
                      </td>

                      <td style={{ padding: '8px 8px' }}>
                        <span style={{
                          fontSize: '10.5px',
                          fontWeight: 500,
                          color: catMeta.color,
                          background: catMeta.bg,
                          border: `1px solid ${catMeta.border}`,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          display: 'inline-block'
                        }}>
                          {catMeta.label}
                        </span>
                      </td>

                      <td style={{ padding: '8px 8px' }}>
                        {lead.reply_status === 'bounced' ? (
                          <span style={{
                            fontSize: '10.5px',
                            fontWeight: 600,
                            color: '#f87171',
                            background: 'rgba(239, 68, 68, 0.15)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            padding: '2px 6px',
                            borderRadius: '4px'
                          }}>
                            Bounced ⚠️
                          </span>
                        ) : (
                          <span className={`badge ${
                            lead.validation_status === 'valid' ? 'badge-valid' :
                            lead.validation_status === 'risky' ? 'badge-risky' :
                            lead.validation_status === 'invalid' ? 'badge-invalid' : ''
                          }`} style={{ fontSize: '10.5px', padding: '2px 6px' }}>
                            {lead.validation_status === 'valid' ? 'Valid ✓' : lead.validation_status || 'Pending'}
                          </span>
                        )}
                      </td>

                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {isReplied ? (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => setViewingReply(lead)}
                              style={{ padding: '3px 7px', fontSize: '10.5px', color: '#4ade80', borderColor: 'rgba(74, 222, 128, 0.4)', background: 'rgba(74, 222, 128, 0.1)' }}
                            >
                              <span>Replied ✓</span>
                            </button>
                          ) : isAutoReply ? (
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => setViewingReply(lead)}
                              style={{ padding: '3px 7px', fontSize: '10.5px', color: '#fbbf24', borderColor: 'rgba(251, 191, 36, 0.4)', background: 'rgba(251, 191, 36, 0.15)' }}
                              title="View Automated Reply"
                            >
                              <span>Auto-Reply 🤖</span>
                            </button>
                          ) : (lead.reply_status === 'bounced' || lead.validation_status === 'invalid') ? (
                            <span style={{ fontSize: '10.5px', color: '#f87171', padding: '2px 6px', fontWeight: 600 }}>
                              Failed ⚠️
                            </span>
                          ) : isContacted ? (
                            <span style={{ fontSize: '10.5px', color: '#60a5fa', background: 'rgba(59, 130, 246, 0.12)', padding: '2px 6px', borderRadius: '4px' }}>
                              Sent ✓
                            </span>
                          ) : (
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              onClick={() => setActiveTab && setActiveTab('campaigns')}
                              style={{ padding: '3px 8px', fontSize: '10.5px' }}
                            >
                              <Mail size={11} />
                              <span>Reach Out</span>
                            </button>
                          )}

                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => setEditingLead({ ...lead })}
                            style={{ padding: '3px 5px' }}
                            title="Edit Buyer"
                          >
                            <Pencil size={11} />
                          </button>

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
                  placeholder="e.g. Send MOQ matrix & follow up on Aug 27"
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

      {/* Reply Snippet Inspection Modal */}
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
