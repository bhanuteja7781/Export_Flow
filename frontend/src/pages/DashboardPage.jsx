import React from 'react';
import Header from '../components/Header';
import { Play, Send, Mail, Users, ShieldCheck, TrendingUp } from 'lucide-react';

const CATEGORY_MAP = {
  'home_decor_retailer': 'Home Décor Retailer',
  'wedding_event_decorator': 'Wedding & Event Stylist',
  'hospitality_hotel': 'Hotel & Hospitality',
  'gift_specialty': 'Gift & Specialty Store',
  'interior_design': 'Interior Design Studio',
  'event_party_rental': 'Event Rental Company',
  'furniture_lifestyle': 'Furniture & Lifestyle',
  'wholesale_distributor': 'Wholesale Distributor'
};

export default function DashboardPage({
  metrics = {},
  leads = [],
  setActiveTab
}) {
  const total = leads.length;
  const deliverable = leads.filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced').length;
  const invalid = leads.filter(l => l.validation_status === 'invalid' || l.reply_status === 'bounced').length;
  const contactedBuyers = leads.filter(l => Boolean(l.last_contacted_at)).length;
  const totalSent = contactedBuyers;
  const deliverabilityRate = total > 0 ? Math.round((deliverable / total) * 100) : 100;

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / OVERVIEW"
        title="Overview"
        subtitle="North American export outreach pipeline and live campaign status."
      />

      {/* Metric Cards */}
      <div className="overview-stats-grid">
        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('leads')}>
          <div className="stat-label">Total Buyers Discovered</div>
          <div className="stat-value">{total}</div>
        </div>

        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('leads')}>
          <div className="stat-label">Deliverable Buyers</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{deliverable} <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-muted)' }}>({deliverabilityRate}%)</span></div>
        </div>

        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('campaigns')}>
          <div className="stat-label">Total Emails Sent</div>
          <div className="stat-value" style={{ color: 'var(--primary)' }}>
            {totalSent} <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-muted)' }}>({contactedBuyers} recipients)</span>
          </div>
        </div>

        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('leads')}>
          <div className="stat-label">Suppressed / Invalid</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>{invalid}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="app-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 className="card-heading" style={{ margin: 0 }}>Quick Actions</h3>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-primary btn-sm" onClick={() => setActiveTab('leads')}>
              <Play size={14} />
              <span>Find Brand New Buyers</span>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('campaigns')}>
              <Send size={14} />
              <span>Compose Campaign &rarr;</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Leads Table */}
      <div className="app-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="card-heading">Recent Discovered Buyers (America & Canada)</h3>
          {leads.length > 0 && (
            <button className="queue-btn-text" onClick={() => setActiveTab('leads')}>
              View All ({leads.length}) &rarr;
            </button>
          )}
        </div>

        <div className="app-table-container">
          <table className="app-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ padding: '10px 14px' }}>Company / Contact</th>
                <th style={{ padding: '10px 14px' }}>Region</th>
                <th style={{ padding: '10px 14px' }}>Commercial Buyer Type</th>
                <th style={{ padding: '10px 14px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No buyer leads yet. Click "Find Brand New Buyers" to begin prospecting.
                  </td>
                </tr>
              ) : (
                leads.slice(0, 6).map((lead) => {
                  const isContacted = Boolean(lead.last_contacted_at);
                  const isInvalid = lead.validation_status === 'invalid' || lead.reply_status === 'bounced';

                  return (
                    <tr key={lead.id || lead.email}>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '12.5px' }}>
                          {lead.company_name || lead.buyer_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{lead.email}</div>
                      </td>
                      <td style={{ padding: '10px 14px', fontSize: '11.5px' }}>{lead.country || 'USA'}</td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                          {CATEGORY_MAP[lead.category] || 'Home Décor Retailer'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        {isInvalid ? (
                          <span style={{ fontSize: '10.5px', color: '#f87171', background: 'rgba(239, 68, 68, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                            Suppressed
                          </span>
                        ) : isContacted ? (
                          <span style={{ fontSize: '10.5px', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.12)', padding: '2px 6px', borderRadius: '4px' }}>
                            Sent
                          </span>
                        ) : (
                          <span className={`badge ${lead.validation_status === 'valid' ? 'badge-valid' : 'badge-risky'}`} style={{ fontSize: '10.5px' }}>
                            {lead.validation_status || 'Deliverable'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
