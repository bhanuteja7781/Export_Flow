import React from 'react';
import Header from '../components/Header';
import { TrendingUp, ShieldCheck, Mail, CheckCircle2, Building2, Store, Sparkles } from 'lucide-react';

export default function AnalyticsPage({ metrics = {}, leads = [] }) {
  const total = leads.length;
  const delivered = leads.filter(l => Boolean(l.last_contacted_at) && l.reply_status !== 'bounced').length;
  const deliverable = leads.filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced').length;
  const invalid = leads.filter(l => l.validation_status === 'invalid' || l.reply_status === 'bounced').length;
  const totalAttempts = delivered;
  const replied = leads.filter(l => l.reply_status === 'replied').length;

  const wholesale = leads.filter(l => l.category === 'wholesale_distributor').length;
  const retailers = leads.filter(l => ['home_decor_retailer', 'gift_specialty', 'furniture_lifestyle'].includes(l.category)).length;
  const hospitalityAndEvents = leads.filter(l => ['wedding_event_decorator', 'hospitality_hotel', 'interior_design', 'event_party_rental'].includes(l.category)).length;

  const deliverabilityRate = total > 0 ? Math.round((deliverable / total) * 100) : 100;
  const wholesaleRate = total > 0 ? Math.round((wholesale / total) * 100) : 0;
  const domainHealthScore = total > 0 ? Math.max(50, Math.round(100 - (invalid / total) * 30)) : 100;

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / ANALYTICS"
        title="Performance Analytics"
        subtitle="End-to-end pipeline metrics across prospect discovery, MX validation, and Gmail dispatch."
      />

      <div className="overview-stats-grid" style={{ marginBottom: '24px' }}>
        <div className="overview-stat-card">
          <div className="stat-label">Deliverability Rate</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{deliverabilityRate}%</div>
        </div>

        <div className="overview-stat-card">
          <div className="stat-label">Total Outbound Sent</div>
          <div className="stat-value" style={{ color: 'var(--primary)' }}>{totalAttempts}</div>
        </div>

        <div className="overview-stat-card">
          <div className="stat-label">Successfully Delivered</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{delivered}</div>
        </div>

        <div className="overview-stat-card">
          <div className="stat-label">Domain Health Score</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{domainHealthScore} / 100</div>
        </div>
      </div>

      <div className="app-card" style={{ marginBottom: '24px' }}>
        <h2 className="card-heading" style={{ marginBottom: '16px' }}>Commercial Pipeline Funnel</h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Step 1 */}
          <div style={{
            padding: '14px 18px',
            background: '#070b14',
            borderRadius: '6px',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
              <span>1. Total North American Prospects Discovered</span>
              <span>{total} buyers</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: '100%', height: '100%', background: 'var(--primary)', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Step 2 */}
          <div style={{
            padding: '14px 18px',
            background: '#070b14',
            borderRadius: '6px',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
              <span>2. Deliverable Buyers (Valid & Active Mailboxes)</span>
              <span>{deliverable} deliverable &bull; {invalid} suppressed</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: total > 0 ? `${Math.round((deliverable / total) * 100)}%` : '0%', height: '100%', background: 'var(--success)', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Step 3 */}
          <div style={{
            padding: '14px 18px',
            background: '#070b14',
            borderRadius: '6px',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
              <span>3. Commercial Segment Breakdown</span>
              <span>{retailers} Retailers &bull; {hospitalityAndEvents} Hospitality/Design &bull; {wholesale} Wholesalers</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: total > 0 ? `${Math.round((deliverable / total) * 100)}%` : '0%', height: '100%', background: '#a855f7', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Step 4 */}
          <div style={{
            padding: '14px 18px',
            background: '#070b14',
            borderRadius: '6px',
            border: '1px solid var(--border-color)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
              <span>4. Dispatched via Gmail SMTP Outreach</span>
              <span>{totalAttempts} emails dispatched &bull; {delivered} actually delivered to buyers</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: totalAttempts > 0 ? `${Math.round((delivered / totalAttempts) * 100)}%` : '0%', height: '100%', background: '#3b82f6', borderRadius: '3px' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
