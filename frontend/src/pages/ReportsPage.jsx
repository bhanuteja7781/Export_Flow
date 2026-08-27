import React, { useState, useMemo, useEffect } from 'react';
import Header from '../components/Header';
import {
  Download,
  Search,
  Copy,
  Check,
  FileSpreadsheet,
  FileText,
  MailCheck,
  Users,
  Edit3,
  ExternalLink,
  Calendar,
  Clock,
  RotateCcw,
  ShieldAlert,
  X
} from 'lucide-react';

const parseDateToTime = (dateStr, fallback = 0) => {
  if (!dateStr) return fallback;
  if (typeof dateStr === 'number') return dateStr;
  const s = String(dateStr).trim();

  // 1. Check for ISO string with T / Z
  if (s.includes('T') || s.includes('Z')) {
    const t = new Date(s).getTime();
    if (!isNaN(t)) return t;
  }

  // 2. Check for DD/MM/YYYY or D/M/YYYY (e.g. 24/8/2026 or 25/7/2026)
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

  // 3. Check for YYYY-MM-DD
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


const downloadFile = (url, defaultName) => {
  try {
    const a = document.createElement("a");
    a.href = url;
    if (defaultName) a.download = defaultName;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      if (document.body.contains(a)) document.body.removeChild(a);
    }, 150);
  } catch (e) {
    window.open(url, "_blank");
  }
};

const getCleanWebsiteUrl = (raw) => {
  if (!raw) return null;
  const s = String(raw).trim();
  if (!s || s.toLowerCase() === "n/a" || s === "-" || s.toLowerCase() === "none" || s.toLowerCase() === "null") return null;
  if (s.startsWith("http://") || s.startsWith("https://")) return s;
  if (s.includes(".") && !s.includes(" ")) return `https://${s}`;
  return null;
};

const getDisplayDomain = (raw) => {
  if (!raw) return "";
  return String(raw).replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0];
};

export default function ReportsPage({
  onDownloadCSV,
  onDownloadPDF,
  onUpdateLead,
  onRecheckAndClean,
  isRechecking = false,
  metrics = {},
  leads = [],
  settings = {},
  setActiveTab
}) {
  const [activeReportTab, setActiveReportTab] = useState('sent_log');
  const [logTimeframe, setLogTimeframe] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [responseFilter, setResponseFilter] = useState('all');
  const [copiedSentLog, setCopiedSentLog] = useState(false);
  const [copiedBuyers, setCopiedBuyers] = useState(false);
  const [sentLogRows, setSentLogRows] = useState([]);
  const [isLoadingSentLogs, setIsLoadingSentLogs] = useState(false);

  const [editingLead, setEditingLead] = useState(null);
  const [editFeedback, setEditFeedback] = useState('');
  const [editFollowUp, setEditFollowUp] = useState('');
  const [editResponses, setEditResponses] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleRecheckMail = async () => {
    if (onRecheckAndClean) {
      await onRecheckAndClean();
      await fetchSentLogs();
    }
  };

  const fetchSentLogs = async (timeframe = logTimeframe) => {
    setIsLoadingSentLogs(true);
    try {
      const res = await fetch(`/api/sent_log/data?timeframe=${timeframe}`);
      if (res.ok) {
        const data = await res.json();
        setSentLogRows(data.rows || []);
      }
    } catch (err) {
      console.error('Failed to fetch sent log data:', err);
    } finally {
      setIsLoadingSentLogs(false);
    }
  };

  useEffect(() => {
    fetchSentLogs(logTimeframe);
  }, [logTimeframe]);

  const formatLeadRow = (l) => {
    let dateVal = l.date;
    if (!dateVal) {
      const rawDate = l.last_contacted_at || l.discovered_at;
      if (rawDate) {
        try {
          const d = new Date(rawDate);
          dateVal = `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
        } catch {
          dateVal = '24/8/2026';
        }
      } else {
        dateVal = '24/8/2026';
      }
    }

    const company = l.company_name || l.buyer_name || 'Discovered Business';
    const email = l.email || '';
    let website = l.website || '';
    if (!website && email.includes('@')) {
      website = `https://www.${email.split('@')[1]}`;
    }

    let responses = l.responses;
    if (l.reply_status === 'auto_reply' || (responses && (responses.toLowerCase().includes('automated') || responses.toLowerCase().includes('auto-reply')))) {
      responses = 'Automated Reply';
    } else if (l.reply_status === 'replied' || (responses && responses.toLowerCase().includes('replied') && !responses.toLowerCase().includes('awaiting'))) {
      responses = l.reply_snippet ? `Replied: ${l.reply_snippet}` : (responses && !responses.startsWith('Catalog Dispatched') ? responses : 'Replied: Requested wholesale pricing & MOQ');
    } else if (l.reply_status === 'bounced' || l.validation_status === 'invalid') {
      responses = 'Invalid Email (Bounced)';
    } else if (l.last_contacted_at || (responses && responses.includes('Awaiting Reply'))) {
      responses = '(Awaiting Reply)';
    } else {
      responses = 'Pending Initial Outreach';
    }

    let feedback = l.intern_feedback;
    if (!feedback) {
      feedback = l.classification_reason || `${company}: Verified commercial B2B buyer for handcrafted metal candle holders & lanterns.`;
    }

    let followUp = l.follow_ups || l.followup;
    if (!followUp) {
      if (l.reply_status === 'replied') {
        followUp = 'Send wholesale price list, MOQ breakdown & custom catalog';
      } else if (l.reply_status === 'auto_reply') {
        followUp = 'Set reminder to follow up 3 business days post-return';
      } else if (l.last_contacted_at) {
        followUp = 'Follow-up #1 scheduled in 3 days with highlight deck';
      } else {
        followUp = 'Ready for initial catalog outreach dispatch';
      }
    }

    return {
      id: l.id || l.email,
      date: dateVal,
      company,
      email,
      website,
      responses,
      feedback,
      followUp,
      raw_date: l.last_contacted_at || l.date || l.discovered_at || dateVal,
      raw: l
    };
  };

  const allBuyersRows = useMemo(() => {
    const list = leads.map(formatLeadRow).filter(item => {
      if (responseFilter === 'replied' && !item.responses.toLowerCase().includes('replied')) return false;
      if (responseFilter === 'auto_reply' && !item.responses.toLowerCase().includes('auto-reply') && !item.responses.toLowerCase().includes('automated')) return false;
      if (responseFilter === 'dispatched' && !item.responses.toLowerCase().includes('dispatched') && !item.responses.toLowerCase().includes('awaiting')) return false;
      if (responseFilter === 'pending' && !item.responses.toLowerCase().includes('pending')) return false;

      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase();
        return (
          item.company.toLowerCase().includes(q) ||
          item.email.toLowerCase().includes(q) ||
          item.website.toLowerCase().includes(q) ||
          item.responses.toLowerCase().includes(q) ||
          item.feedback.toLowerCase().includes(q) ||
          item.followUp.toLowerCase().includes(q) ||
          item.date.toLowerCase().includes(q)
        );
      }
      return true;
    });

    // STRICT REVERSE CHRONOLOGICAL SORT (Newest First on top: 26/8 -> 25/8 -> 24/8 ...)
    return list.sort((a, b) => {
      const timeA = parseDateToTime(a.raw?.discovered_at || a.raw_date || a.date, 0);
      const timeB = parseDateToTime(b.raw?.discovered_at || b.raw_date || b.date, 0);
      return timeB - timeA;
    });
  }, [leads, responseFilter, searchTerm]);

  const filteredSentLogs = useMemo(() => {
    const list = sentLogRows.filter(item => {
      const resp = item['RESPONSES'] || '';
      // Exclude any bounced, invalid, or undispatched/pending initial outreach attempts from Sent Log
      if (resp.toLowerCase().includes('bounced') || resp.toLowerCase().includes('invalid') || resp.toLowerCase().includes('pending')) {
        return false;
      }

      if (responseFilter === 'replied' && !resp.toLowerCase().includes('replied')) return false;
      if (responseFilter === 'auto_reply' && !resp.toLowerCase().includes('auto-reply') && !resp.toLowerCase().includes('automated')) return false;
      if (responseFilter === 'dispatched' && !resp.toLowerCase().includes('dispatched') && !resp.toLowerCase().includes('awaiting')) return false;
      if (responseFilter === 'pending' && !resp.toLowerCase().includes('pending')) return false;

      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase();
        const comp = (item['NAME OF THE COMPANY'] || '').toLowerCase();
        const em = (item['EMAIL ADDRESS'] || '').toLowerCase();
        const web = (item['WEBSITE LINK'] || '').toLowerCase();
        const fb = (item["INTERN'S FEEDBACK"] || '').toLowerCase();
        const fol = (item['Follow-ups'] || '').toLowerCase();
        const dt = (item['DATE'] || '').toLowerCase();
        return (
          comp.includes(q) ||
          em.includes(q) ||
          web.includes(q) ||
          resp.toLowerCase().includes(q) ||
          fb.includes(q) ||
          fol.includes(q) ||
          dt.includes(q)
        );
      }
      return true;
    });

    // STRICT CHRONOLOGICAL SORT (Oldest First: 24/8 -> 25/8 -> 26/8 ...)
    return list.sort((a, b) => {
      const timeA = parseDateToTime(a.raw_sent_at || a.sent_at || a['DATE'], 0);
      const timeB = parseDateToTime(b.raw_sent_at || b.sent_at || b['DATE'], 0);
      return timeA - timeB;
    });
  }, [sentLogRows, responseFilter, searchTerm]);

  const handleCopySentLogTSV = () => {
    const rows = filteredSentLogs.map(item => [
      item["DATE"],
      item["NAME OF THE COMPANY"],
      item["EMAIL ADDRESS"],
      item["WEBSITE LINK"],
      item["RESPONSES"]
    ].map(val => String(val || '').replace(/\t/g, ' ').replace(/\n/g, ' ')).join('\t'));

    const tsvContent = rows.join('\n');
    navigator.clipboard.writeText(tsvContent).then(() => {
      setCopiedSentLog(true);
      setTimeout(() => setCopiedSentLog(false), 2500);
    });
  };

  const handleDownloadSentLogCSV = () => {
    downloadFile(`/api/export/sent_log?range=${logTimeframe}&format=csv`, `sent_log_${logTimeframe}.csv`);
  };

  const handleDownloadSentLogTSV = () => {
    downloadFile(`/api/export/sent_log?range=${logTimeframe}&format=tsv`, `sent_log_${logTimeframe}.tsv`);
  };

  const handleDownloadBuyersCSV = () => {
    downloadFile('/api/export/buyers?format=csv', 'buyers.csv');
  };

  const handleCopyBuyersTSV = () => {
    const rows = allBuyersRows.map(item => [
      item.date,
      item.company,
      item.email,
      item.website,
      item.responses
    ].map(val => String(val || '').replace(/\t/g, ' ').replace(/\n/g, ' ')).join('\t'));

    const tsvContent = rows.join('\n');
    navigator.clipboard.writeText(tsvContent).then(() => {
      setCopiedBuyers(true);
      setTimeout(() => setCopiedBuyers(false), 2500);
    });
  };

  const openEditModal = (item) => {
    const isSentLogRow = Boolean(item["EMAIL ADDRESS"]);
    const id = isSentLogRow ? item["EMAIL ADDRESS"] : item.id;
    const company = isSentLogRow ? item["NAME OF THE COMPANY"] : item.company;
    const email = isSentLogRow ? item["EMAIL ADDRESS"] : item.email;
    const responses = isSentLogRow ? item["RESPONSES"] : item.responses;

    setEditingLead({ id, company, email });
    setEditResponses(responses || '');
  };

  const handleSaveEdit = async () => {
    if (!editingLead) return;
    setIsSaving(true);
    try {
      const payload = {
        id: editingLead.id,
        email: editingLead.email,
        responses: editResponses
      };
      if (onUpdateLead) {
        await onUpdateLead(payload);
      } else {
        await fetch('/api/leads/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }
      await fetchSentLogs(logTimeframe);
      setEditingLead(null);
    } catch (err) {
      alert("Failed to update: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const contactedCount = leads.filter(l => Boolean(l.last_contacted_at) && l.validation_status !== 'invalid').length;

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / REPORTS"
        title="Reports & Outreach Logs"
        subtitle="Export and copy daily outreach logs, buyer lists, and catalog attachments."
      />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveReportTab('sent_log')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            border: activeReportTab === 'sent_log' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
            background: activeReportTab === 'sent_log' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(15, 23, 42, 0.6)',
            color: activeReportTab === 'sent_log' ? '#ffffff' : 'var(--text-muted)'
          }}
        >
          <MailCheck size={16} color={activeReportTab === 'sent_log' ? '#60a5fa' : 'var(--text-muted)'} />
          <span>Sent Outreach Log</span>
          <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.3)', color: '#93c5fd' }}>
            {sentLogRows.length}
          </span>
        </button>

        <button
          onClick={() => setActiveReportTab('all_buyers')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            border: activeReportTab === 'all_buyers' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
            background: activeReportTab === 'all_buyers' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(15, 23, 42, 0.6)',
            color: activeReportTab === 'all_buyers' ? '#ffffff' : 'var(--text-muted)'
          }}
        >
          <Users size={16} color={activeReportTab === 'all_buyers' ? '#60a5fa' : 'var(--text-muted)'} />
          <span>All Buyers Directory</span>
          <span style={{ fontSize: '11px', padding: '1px 6px', borderRadius: '10px', background: 'rgba(148, 163, 184, 0.2)', color: 'var(--text-muted)' }}>
            {leads.length}
          </span>
        </button>
      </div>

      {/* 1. SENT OUTREACH LOG VIEW */}
      {activeReportTab === 'sent_log' && (
        <div className="app-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <MailCheck size={18} color="#4ade80" />
                <h3 className="card-heading" style={{ margin: 0, fontSize: '16px' }}>
                  Sent Outreach Log
                </h3>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                Audit log of all successfully dispatched buyer emails.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleRecheckMail}
                disabled={isRechecking || isLoadingSentLogs}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderColor: 'rgba(239, 68, 68, 0.3)',
                  color: '#f87171'
                }}
                title="Scan mailbox for bounce notifications (Address not found) and purge invalid buyers from report"
              >
                <RotateCcw size={13} className={isRechecking ? 'animate-spin' : ''} />
                <span>{isRechecking ? 'Rechecking Mail...' : 'Recheck Mail & Purge Bounces'}</span>
              </button>

              <button
                className="btn btn-primary btn-sm"
                onClick={handleCopySentLogTSV}
                style={{
                  background: copiedSentLog ? '#16a34a' : 'var(--primary)',
                  borderColor: copiedSentLog ? '#22c55e' : undefined
                }}
                title="Copy rows to clipboard"
              >
                {copiedSentLog ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedSentLog ? 'Copied to Clipboard!' : 'Copy to Clipboard'}</span>
              </button>

              <button className="btn btn-secondary btn-sm" onClick={handleDownloadSentLogCSV} title="Download CSV">
                <Download size={13} />
                <span>Download CSV</span>
              </button>

              <button className="btn btn-secondary btn-sm" onClick={handleDownloadSentLogTSV} title="Download TSV">
                <Download size={13} />
                <span>TSV</span>
              </button>
            </div>
          </div>

          {/* Timeframe & Search */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', padding: '12px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-secondary)', marginRight: '4px', fontWeight: 600 }}>
                <Calendar size={12} color="var(--primary)" />
                <span>Timeframe:</span>
              </div>
              {[
                { id: 'today', label: 'Today' },
                { id: 'yesterday', label: 'Yesterday' },
                { id: 'week', label: 'This Week' },
                { id: 'month', label: 'This Month' },
                { id: 'all', label: 'All Dispatches' }
              ].map(tf => (
                <button
                  key={tf.id}
                  type="button"
                  onClick={() => setLogTimeframe(tf.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    cursor: 'pointer',
                    border: logTimeframe === tf.id ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    background: logTimeframe === tf.id ? 'rgba(59, 130, 246, 0.25)' : 'transparent',
                    color: logTimeframe === tf.id ? '#ffffff' : 'var(--text-muted)',
                    fontWeight: logTimeframe === tf.id ? 600 : 400
                  }}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1', minWidth: '220px', maxWidth: '380px' }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search sent log..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-main)',
                  fontSize: '12px',
                  width: '100%',
                  outline: 'none'
                }}
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '2px' }}
                >
                  <X size={13} />
                </button>
              )}
            </div>
          </div>

          {/* Table */}
          <div className="app-table-container" style={{ maxHeight: '600px', overflowY: 'auto' }}>
            <table className="app-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'rgba(15, 23, 42, 0.95)', position: 'sticky', top: 0, zIndex: 10 }}>
                  <th style={{ padding: '10px 12px', width: '85px', whiteSpace: 'nowrap' }}>DATE</th>
                  <th style={{ padding: '10px 12px', minWidth: '180px' }}>NAME OF THE COMPANY</th>
                  <th style={{ padding: '10px 12px', minWidth: '180px' }}>EMAIL ADDRESS</th>
                  <th style={{ padding: '10px 12px', minWidth: '140px' }}>WEBSITE LINK</th>
                  <th style={{ padding: '10px 12px', width: '170px', minWidth: '160px', maxWidth: '180px' }}>RESPONSES</th>
                  <th style={{ padding: '10px 10px', width: '50px', textAlign: 'center' }}>Edit</th>
                </tr>
              </thead>
              <tbody>
                {filteredSentLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                      No sent outreach logs found for timeframe "{logTimeframe}".
                    </td>
                  </tr>
                ) : (
                  filteredSentLogs.map((item, idx) => {
                    const resp = item['RESPONSES'] || '';
                    const isReplied = resp.toLowerCase().includes('replied');
                    const isAutoReply = resp.toLowerCase().includes('automated') || resp.toLowerCase().includes('auto-reply');
                    const isDispatched = resp.toLowerCase().includes('awaiting') || resp.toLowerCase().includes('dispatched');

                    return (
                      <tr key={idx} style={{ transition: 'background 0.15s ease' }}>
                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: '11.5px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {item['DATE']}
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-main)' }}>
                          {item['NAME OF THE COMPANY']}
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: '11px' }}>
                          <a
                            href={`mailto:${item['EMAIL ADDRESS']}`}
                            style={{ color: '#93c5fd', textDecoration: 'none' }}
                          >
                            {item['EMAIL ADDRESS']}
                          </a>
                        </td>
                        <td style={{ padding: '10px 12px', fontSize: '11px' }}>
                          {item['WEBSITE LINK'] ? (
                            <a
                              href={item['WEBSITE LINK'].startsWith('http') ? item['WEBSITE LINK'] : `https://${item['WEBSITE LINK']}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}
                            >
                              <span>{item['WEBSITE LINK'].replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]}</span>
                              <ExternalLink size={10} />
                            </a>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                        <td style={{ padding: '10px 12px', width: '170px', maxWidth: '180px', overflow: 'hidden' }}>
                          <div
                            title={resp}
                            style={{
                              display: 'inline-block',
                              maxWidth: '100%',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              verticalAlign: 'middle',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 500,
                              background: isReplied
                                ? 'rgba(74, 222, 128, 0.12)'
                                : isAutoReply
                                  ? 'rgba(251, 191, 36, 0.12)'
                                  : isDispatched
                                    ? 'rgba(59, 130, 246, 0.12)'
                                    : 'rgba(148, 163, 184, 0.08)',
                              color: isReplied
                                ? '#4ade80'
                                : isAutoReply
                                  ? '#fbbf24'
                                  : isDispatched
                                    ? '#60a5fa'
                                    : 'var(--text-muted)',
                              border: `1px solid ${isReplied ? 'rgba(74, 222, 128, 0.3)' : isAutoReply ? 'rgba(251, 191, 36, 0.3)' : isDispatched ? 'rgba(59, 130, 246, 0.3)' : 'rgba(148, 163, 184, 0.2)'
                                }`
                            }}
                          >
                            {resp}
                          </div>
                        </td>
                        <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                          <button
                            onClick={() => openEditModal(item)}
                            style={{
                              background: 'transparent',
                              border: '1px solid var(--border-color)',
                              borderRadius: '4px',
                              padding: '4px',
                              color: 'var(--text-muted)',
                              cursor: 'pointer'
                            }}
                            title="Edit entry"
                          >
                            <Edit3 size={12} />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. ALL BUYERS DIRECTORY VIEW */}
      {activeReportTab === 'all_buyers' && (
        <div className="app-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <Users size={18} color="var(--primary)" />
                <h3 className="card-heading" style={{ margin: 0, fontSize: '16px' }}>
                  All Discovered Buyers Directory ({allBuyersRows.length})
                </h3>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                Registry of all prospective commercial buyers.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleRecheckMail}
                disabled={isRechecking}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderColor: 'rgba(239, 68, 68, 0.3)',
                  color: '#f87171'
                }}
                title="Scan mailbox for bounce notifications (Address not found) and purge invalid buyers from report"
              >
                <RotateCcw size={13} className={isRechecking ? 'animate-spin' : ''} />
                <span>{isRechecking ? 'Rechecking...' : 'Recheck Mail & Purge'}</span>
              </button>

              <button
                className="btn btn-secondary btn-sm"
                onClick={handleCopyBuyersTSV}
                style={{
                  background: copiedBuyers ? 'rgba(74, 222, 128, 0.15)' : undefined,
                  borderColor: copiedBuyers ? '#4ade80' : undefined,
                  color: copiedBuyers ? '#4ade80' : undefined
                }}
              >
                {copiedBuyers ? <Check size={13} /> : <Copy size={13} />}
                <span>{copiedBuyers ? 'Copied!' : 'Copy to Clipboard'}</span>
              </button>

              <button className="btn btn-primary btn-sm" onClick={handleDownloadBuyersCSV}>
                <Download size={13} />
                <span>Download CSV</span>
              </button>
            </div>
          </div>

          <div className="app-table-container" style={{ maxHeight: '600px', overflowY: 'auto' }}>
            <table className="app-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ background: 'rgba(15, 23, 42, 0.95)', position: 'sticky', top: 0, zIndex: 10 }}>
                  <th style={{ padding: '10px 12px', width: '85px', whiteSpace: 'nowrap' }}>DATE</th>
                  <th style={{ padding: '10px 12px', minWidth: '180px' }}>NAME OF THE COMPANY</th>
                  <th style={{ padding: '10px 12px', minWidth: '180px' }}>EMAIL ADDRESS</th>
                  <th style={{ padding: '10px 12px', minWidth: '140px' }}>WEBSITE LINK</th>
                  <th style={{ padding: '10px 12px', width: '170px', minWidth: '160px', maxWidth: '180px' }}>RESPONSES</th>
                  <th style={{ padding: '10px 10px', width: '50px', textAlign: 'center' }}>Edit</th>
                </tr>
              </thead>
              <tbody>
                {allBuyersRows.map((item, idx) => {
                  const resp = item.responses || '';
                  const isReplied = resp.toLowerCase().includes('replied');
                  const isAutoReply = resp.toLowerCase().includes('automated') || resp.toLowerCase().includes('auto-reply');
                  const isDispatched = resp.toLowerCase().includes('awaiting') || resp.toLowerCase().includes('dispatched');

                  return (
                    <tr key={item.id || idx}>
                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {item.date}
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--text-main)' }}>
                          {item.company}
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: '11px' }}>
                          <a href={`mailto:${item.email}`} style={{ color: '#93c5fd', textDecoration: 'none' }}>
                            {item.email}
                          </a>
                        </td>
                        <td style={{ padding: '10px 12px', fontSize: '11px' }}>
                          {item.website ? (
                            <a
                              href={item.website.startsWith('http') ? item.website : `https://${item.website}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}
                            >
                              <span>{item.website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]}</span>
                              <ExternalLink size={10} />
                            </a>
                          ) : '—'}
                        </td>
                        <td style={{ padding: '10px 12px', width: '170px', maxWidth: '180px', overflow: 'hidden' }}>
                          <div
                            title={resp}
                            style={{
                              display: 'inline-block',
                              maxWidth: '100%',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              verticalAlign: 'middle',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 500,
                              background: isReplied
                                ? 'rgba(74, 222, 128, 0.12)'
                                : isAutoReply
                                  ? 'rgba(251, 191, 36, 0.15)'
                                  : isDispatched
                                    ? 'rgba(59, 130, 246, 0.12)'
                                    : 'rgba(148, 163, 184, 0.08)',
                              color: isReplied
                                ? '#4ade80'
                                : isAutoReply
                                  ? '#fbbf24'
                                  : isDispatched
                                    ? '#60a5fa'
                                    : 'var(--text-muted)',
                              border: `1px solid ${isReplied ? 'rgba(74, 222, 128, 0.3)' : isAutoReply ? 'rgba(251, 191, 36, 0.4)' : isDispatched ? 'rgba(59, 130, 246, 0.3)' : 'rgba(148, 163, 184, 0.2)'
                                }`
                            }}
                          >
                            {resp}
                          </div>
                        </td>
                    <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                      <button
                        onClick={() => openEditModal(item)}
                        style={{ background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '4px', color: 'var(--text-muted)', cursor: 'pointer' }}
                      >
                        <Edit3 size={12} />
                      </button>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Catalog PDF Download */}
      <div className="app-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={20} color="#c084fc" />
          <div>
            <h4 style={{ margin: 0, fontSize: '13px', color: 'var(--text-main)' }}>Catalog PDF Attachment (Candle_Holders.pdf)</h4>
            <div style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Official Product Zone International catalog attachment.</div>
          </div>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onDownloadPDF}>
          <Download size={13} />
          <span>Download Catalog PDF</span>
        </button>
      </div>

      {/* Edit Modal */}
      {editingLead && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="app-card" style={{ width: '100%', maxWidth: '460px', padding: '24px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--text-main)' }}>
                  Edit Outreach Entry
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--primary)', marginTop: '2px' }}>
                  {editingLead.company} ({editingLead.email})
                </div>
              </div>
              <button
                onClick={() => setEditingLead(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  RESPONSES STATUS / NOTE:
                </label>
                <input
                  type="text"
                  value={editResponses}
                  onChange={(e) => setEditResponses(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: '#070c17',
                    color: 'var(--text-main)',
                    fontSize: '12px'
                  }}
                  placeholder="e.g. (Awaiting Reply) / Automated Reply / Replied..."
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '20px' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setEditingLead(null)}
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSaveEdit}
                disabled={isSaving}
              >
                {isSaving ? 'Saving...' : 'Save & Sync'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
