import React from 'react';
import Header from '../components/Header';
import { TrendingUp, ShieldCheck, Mail, CheckCircle2, Building2, Store, Sparkles, Globe2, Layers } from 'lucide-react';

export default function AnalyticsPage({ metrics = {}, leads = [] }) {
  const total = leads.length;
  const delivered = leads.filter(l => Boolean(l.last_contacted_at) && l.reply_status !== 'bounced').length;
  const deliverable = leads.filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced').length;
  const invalid = leads.filter(l => l.validation_status === 'invalid' || l.reply_status === 'bounced').length;
  const totalAttempts = delivered;
  const replied = leads.filter(l => l.reply_status === 'replied').length;

  const diaspora = leads.filter(l => l.category === 'diaspora_ethnic' || l.market_segment === 'diaspora').length;
  const wholesale = leads.filter(l => l.category === 'wholesale_distributor' || l.buyer_size === 'enterprise_large').length;
  const furniture = leads.filter(l => l.category === 'furniture_lifestyle').length;
  const homeDecor = leads.filter(l => l.category === 'home_decor_retailer').length;
  const otherSpecialty = leads.filter(l => ['gift_specialty', 'interior_design', 'hospitality_events', 'wedding_event_decorator'].includes(l.category)).length;

  const largeScale = leads.filter(l => l.buyer_size === 'enterprise_large').length;
  const midScale = leads.filter(l => l.buyer_size === 'mid_market').length;
  const independentScale = leads.filter(l => !l.buyer_size || l.buyer_size === 'independent_small').length;

  const deliverabilityRate = total > 0 ? Math.round((deliverable / total) * 100) : 100;
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

      {/* Pipeline Funnel */}
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
              <span>1. Total Commercial Prospects Discovered</span>
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
              <span>3. Target Market Breakdown</span>
              <span>{diaspora} Diaspora &bull; {wholesale} Wholesale &bull; {furniture} Furniture &bull; {homeDecor} Home Décor</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: total > 0 ? `${Math.round((deliverable / total) * 100)}%` : '0%', height: '100%', background: '#f59e0b', borderRadius: '3px' }} />
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
              <span>4. Buyer Scale & Sizing Distribution</span>
              <span>{largeScale} Large Wholesalers &bull; {midScale} Mid-Market Chains &bull; {independentScale} Independent/Diaspora</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#162035', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: total > 0 ? `${Math.round((deliverable / total) * 100)}%` : '0%', height: '100%', background: '#818cf8', borderRadius: '3px' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
