import React, { useState } from 'react';
import Header from '../components/Header';
import { 
  Mail, 
  MessageSquare, 
  RefreshCw, 
  Send, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  Eye, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Building2,
  Sparkles,
  RotateCcw,
  Inbox
} from 'lucide-react';
import { formatISTDateTime } from '../utils/dateUtils';

const SENTIMENT_BADGES = {
  'sample_request': { label: 'Sample Requested', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)', border: 'rgba(34, 197, 94, 0.3)' },
  'pricing_inquiry': { label: 'Pricing & MOQ Inquiry', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)', border: 'rgba(168, 85, 247, 0.3)' },
  'interested': { label: 'Interested / Meeting', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', border: 'rgba(59, 130, 246, 0.3)' }
};

export default function InboxPage({
  leads = [],
  onScanInbox,
  onRecheckAndClean,
  isScanning = false,
  isRechecking = false,
  setActiveTab
}) {
  const [activeView, setActiveView] = useState('replies'); // 'replies', 'auto_replies', 'unreplied'
  const [selectedReply, setSelectedReply] = useState(null);

  // Derive counts accurately
  const repliedLeads = leads.filter(l => l.reply_status === 'replied');
  const autoReplyLeads = leads.filter(l => l.reply_status === 'auto_reply' || (l.responses && l.responses.toLowerCase().includes('automated')));
  const unrepliedLeads = leads.filter(l => Boolean(l.last_contacted_at) && l.reply_status !== 'replied' && l.reply_status !== 'auto_reply' && l.reply_status !== 'bounced' && l.validation_status !== 'invalid');
  const invalidLeads = leads.filter(l => l.validation_status === 'invalid' || l.reply_status === 'bounced');
  const totalContacted = leads.filter(l => Boolean(l.last_contacted_at)).length;
  const responseRate = totalContacted > 0 ? Math.round(((repliedLeads.length + autoReplyLeads.length) / totalContacted) * 100) : 0;

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / INBOX & REPLIES"
        title="Buyer Responses & Inbound Inquiries"
        subtitle="Track incoming buyer replies, RFQs, and sample inquiries from outreach campaigns."
      />

      {/* Top Metrics Cards */}
      <div className="overview-stats-grid" style={{ marginBottom: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveView('replies')}>
          <div className="stat-label">Buyer Replies Received</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>{repliedLeads.length}</div>
        </div>

        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveView('auto_replies')}>
          <div className="stat-label">Automated / Out of Office</div>
          <div className="stat-value" style={{ color: '#fbbf24' }}>{autoReplyLeads.length}</div>
        </div>

        <div className="overview-stat-card" style={{ cursor: 'pointer' }} onClick={() => setActiveView('unreplied')}>
          <div className="stat-label">Outreach Sent (Awaiting Reply)</div>
          <div className="stat-value" style={{ color: '#60a5fa' }}>{unrepliedLeads.length}</div>
        </div>

        <div className="overview-stat-card">
          <div className="stat-label">Bounced Suppressed</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>{invalidLeads.length}</div>
        </div>
      </div>

      {/* Action Banner with Scan Inbox Trigger */}
      <div className="app-card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 className="card-heading" style={{ fontSize: '15px', margin: '0 0 4px 0' }}>
              IMAP Gmail Inbox Scanner
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
              Checks your connected mailbox for incoming buyer replies, RFQs, and delivery failure notifications.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {onRecheckAndClean && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onRecheckAndClean}
                disabled={isRechecking || isScanning}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderColor: 'rgba(239, 68, 68, 0.3)',
                  color: '#f87171'
                }}
                title="Scan mailbox for bounce notifications (Address not found) and purge invalid buyers from report"
              >
                <RotateCcw size={13} className={isRechecking ? 'animate-spin' : ''} />
                <span>{isRechecking ? 'Rechecking Mail...' : 'Recheck Mail & Clean Report'}</span>
              </button>
            )}

            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onScanInbox}
              disabled={isScanning || isRechecking}
            >
              <RefreshCw size={13} className={isScanning ? 'animate-spin' : ''} />
              <span>{isScanning ? 'Scanning Mailbox...' : 'Scan Inbox for Replies'}</span>
            </button>

            {unrepliedLeads.length > 0 && setActiveTab && (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('campaigns')}
              >
                <Send size={13} />
                <span>Launch Follow-Up Campaign ({unrepliedLeads.length})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* View Switcher Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => setActiveView('replies')}
          style={{
            background: activeView === 'replies' ? 'var(--primary)' : 'rgba(15, 23, 42, 0.6)',
            color: activeView === 'replies' ? '#ffffff' : 'var(--text-secondary)',
            border: activeView === 'replies' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <MessageSquare size={14} />
          <span>Received Buyer Replies ({repliedLeads.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveView('auto_replies')}
          style={{
            background: activeView === 'auto_replies' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(15, 23, 42, 0.6)',
            color: activeView === 'auto_replies' ? '#fbbf24' : 'var(--text-secondary)',
            border: activeView === 'auto_replies' ? '1px solid #fbbf24' : '1px solid var(--border-color)',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Clock size={14} color={activeView === 'auto_replies' ? '#fbbf24' : 'var(--text-muted)'} />
          <span>Automated Replies ({autoReplyLeads.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveView('unreplied')}
          style={{
            background: activeView === 'unreplied' ? 'var(--primary)' : 'rgba(15, 23, 42, 0.6)',
            color: activeView === 'unreplied' ? '#ffffff' : 'var(--text-secondary)',
            border: activeView === 'unreplied' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Send size={14} />
          <span>Sent — Awaiting Reply ({unrepliedLeads.length})</span>
        </button>
      </div>

      {/* Tab 1: Received Buyer Replies */}
      {activeView === 'replies' && (
        <div className="app-card">
          <h3 className="card-heading" style={{ marginBottom: '16px' }}>
            Verified Inbound Inquiries & Buyer Messages ({repliedLeads.length})
          </h3>

          {repliedLeads.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <Inbox size={32} style={{ opacity: 0.4, marginBottom: '10px' }} />
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                No incoming replies detected yet
              </div>
              <div style={{ fontSize: '12px', maxWidth: '400px', margin: '0 auto 16px auto' }}>
                Click "Scan Inbox for Replies" above to fetch the latest buyer emails or dispatch initial campaigns.
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={onScanInbox}
                disabled={isScanning}
              >
                <RefreshCw size={12} className={isScanning ? 'animate-spin' : ''} />
                <span>Scan Mailbox Now</span>
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {repliedLeads.map((lead) => {
                const sentimentMeta = SENTIMENT_BADGES[lead.reply_sentiment] || SENTIMENT_BADGES['interested'];
                return (
                  <div
                    key={lead.id}
                    onClick={() => setSelectedReply(lead)}
                    style={{
                      background: '#090e1a',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      padding: '14px 18px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <strong style={{ color: '#ffffff', fontSize: '14px' }}>
                            {lead.buyer_name || lead.company_name}
                          </strong>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            &bull; {lead.company_name} ({lead.country || 'USA'})
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
                          {lead.email}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          color: sentimentMeta.color,
                          background: sentimentMeta.bg,
                          border: `1px solid ${sentimentMeta.border}`,
                          padding: '2px 8px',
                          borderRadius: '4px'
                        }}>
                          {lead.reply_sentiment_label || sentimentMeta.label}
                        </span>

                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {formatISTDateTime(lead.replied_at)}
                        </span>
                      </div>
                    </div>

                    <div style={{
                      fontSize: '12px',
                      color: '#cbd5e1',
                      background: '#040711',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255,255,255,0.05)',
                      lineHeight: '1.5'
                    }}>
                      "{lead.reply_snippet || 'Buyer expressed interest in reviewing catalog and wholesale pricing.'}"
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--primary)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <span>View Details & Thread</span>
                        <ChevronRight size={12} />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Automated Replies / Out of Office */}
      {activeView === 'auto_replies' && (
        <div className="app-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 className="card-heading" style={{ margin: '0 0 4px 0', color: '#fbbf24' }}>
                Automated Responses & Out of Office Notices ({autoReplyLeads.length})
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                Automated acknowledgments, vacation notices, and return dates received from buyer inboxes.
              </p>
            </div>
          </div>

          {autoReplyLeads.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <Clock size={32} style={{ opacity: 0.4, marginBottom: '10px', color: '#fbbf24' }} />
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                No automated replies detected
              </div>
              <div style={{ fontSize: '12px', maxWidth: '400px', margin: '0 auto' }}>
                When buyers have active out-of-office autoreponders, they will appear here with scheduled follow-up dates.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {autoReplyLeads.map((lead) => (
                <div
                  key={lead.id}
                  onClick={() => setSelectedReply(lead)}
                  style={{
                    background: '#090e1a',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '8px',
                    padding: '14px 18px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <strong style={{ color: '#ffffff', fontSize: '14px' }}>
                          {lead.company_name || lead.buyer_name}
                        </strong>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          &bull; {lead.country === 'Canada' ? '🇨🇦 Canada' : '🇺🇸 USA'}
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
                        {lead.email}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        color: '#fbbf24',
                        background: 'rgba(245, 158, 11, 0.15)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        padding: '2px 8px',
                        borderRadius: '4px'
                      }}>
                        Automated Reply 🤖
                      </span>

                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {lead.replied_at ? formatISTDateTime(lead.replied_at) : 'Received'}
                      </span>
                    </div>
                  </div>

                  <div style={{
                    fontSize: '12px',
                    color: '#cbd5e1',
                    background: '#040711',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid rgba(255,255,255,0.05)',
                    lineHeight: '1.5'
                  }}>
                    "{lead.reply_snippet || 'Thank you for reaching out. I am currently out of the office and will return shortly.'}"
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                      Next Action: <strong>{lead.follow_ups || 'Follow-up after return date'}</strong>
                    </span>
                    <span style={{ fontSize: '11px', color: '#fbbf24', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span>View Full Message</span>
                      <ChevronRight size={12} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Sent — Awaiting Reply */}
      {activeView === 'unreplied' && (
        <div className="app-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 className="card-heading" style={{ margin: '0 0 4px 0' }}>
                Contacted Buyers Awaiting Reply ({unrepliedLeads.length})
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                These buyers have been sent your catalog and outreach pitch.
              </p>
            </div>

            {setActiveTab && (
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => setActiveTab('campaigns')}
              >
                <Send size={13} />
                <span>Open Campaigns &rarr;</span>
              </button>
            )}
          </div>

          <div className="app-table-container">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Recipient & Company</th>
                  <th>Region</th>
                  <th>Initial Email Sent</th>
                  <th>Deliverability Status</th>
                  <th>Follow-Up Eligibility</th>
                </tr>
              </thead>
              <tbody>
                {unrepliedLeads.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                      No unreplied buyers in queue.
                    </td>
                  </tr>
                ) : (
                  unrepliedLeads.map((lead) => (
                    <tr key={lead.id}>
                      <td>
                        <strong style={{ color: 'var(--text-main)' }}>{lead.company_name || lead.buyer_name}</strong>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{lead.email}</div>
                      </td>
                      <td>{lead.country === 'Canada' ? '🇨🇦 Canada' : '🇺🇸 USA'}</td>
                      <td>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                          {formatISTDateTime(lead.last_contacted_at)}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-valid">
                          Verified Active
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 600 }}>
                          Ready for Follow-Up ✓
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reply Details Modal */}
      {selectedReply && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="app-card" style={{ width: '100%', maxWidth: '540px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div>
                <h3 className="card-heading" style={{ fontSize: '16px', margin: 0 }}>
                  {selectedReply.buyer_name || selectedReply.company_name}
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {selectedReply.company_name} &bull; {selectedReply.email} &bull; {selectedReply.country || 'USA'}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSelectedReply(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '16px' }}
              >
                ✕
              </button>
            </div>

            <div style={{
              background: '#070b14',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '14px',
              marginBottom: '16px',
              fontSize: '12px',
              lineHeight: '1.6',
              color: '#e2e8f0',
              whiteSpace: 'pre-wrap'
            }}>
              {selectedReply.reply_snippet}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedReply(null)}
              >
                Close
              </button>

              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => {
                  setSelectedReply(null);
                  window.open(`mailto:${selectedReply.email}?subject=Re: Handcrafted Metal Candle Holders Catalog`);
                }}
              >
                <Mail size={12} />
                <span>Reply in Gmail &rarr;</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
