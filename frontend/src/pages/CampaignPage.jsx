import React, { useState, useRef, useEffect } from 'react';
import Header from '../components/Header';
import { 
  Send, 
  Play, 
  Loader2, 
  Mail, 
  FileText, 
  CheckCircle2, 
  Zap, 
  X, 
  Upload, 
  Trash2, 
  Sparkles, 
  Users, 
  AlertCircle, 
  ChevronDown, 
  ChevronUp,
  Download
} from 'lucide-react';

const B2B_EMAIL_TEMPLATES = [
  {
    id: 'tpl-catalog-intro',
    name: 'Version 1: Catalog Introduction',
    badge: 'Friendly Intro',
    subject: 'Handcrafted {{product}} catalog for {{company}}',
    body: `Hi there,

Hope you're having a great week!

I came across {{company}} and wanted to introduce Product Zone International. We manufacture handcrafted {{product}}, metal lanterns, and tabletop decor.

I've attached our 2026 catalog showcasing our complete collection and latest designs for your review.

Would love to know your thoughts on our pieces!

Warm regards,

Product Zone International
Email: {{sender_email}}`
  },
  {
    id: 'tpl-quick-share',
    name: 'Version 2: Quick Lookbook Share',
    badge: 'Short & Sweet',
    subject: 'New {{product}} collection for {{company}}',
    body: `Hi there,

Hope all is well with you!

I'm reaching out to share our latest collection of handcrafted {{product}} and metal tabletop decor.

I've attached our 2026 lookbook for {{company}} to browse through.

Hope you find our designs interesting, and please feel free to reach out if you have any questions!

Best regards,

Product Zone International
Email: {{sender_email}}`
  },
  {
    id: 'tpl-2026-collection',
    name: 'Version 3: New 2026 Collection',
    badge: 'New Designs',
    subject: 'Our new 2026 {{product}} collection for {{company}}',
    body: `Hi there,

Hope your week is going well!

We just launched our new 2026 collection of handcrafted {{product}}, candle lanterns, and centerpiece designs.

Attached is our product catalog showing our full collection and metal finishes (brass, matte black, and bronze).

Hope you enjoy looking through our pieces for {{company}}!

Warm regards,

Product Zone International
Email: {{sender_email}}`
  },
  {
    id: 'tpl-aesthetic-fit',
    name: 'Version 4: Curated Collection Fit',
    badge: 'Aesthetic Fit',
    subject: '{{product}} collection lookbook for {{company}}',
    body: `Hi there,

Hope you're having a wonderful day!

I really admire the curation at {{company}} and thought our handcrafted {{product}} and metal decor pieces would be a great fit for your collection.

I've attached our latest catalog showcasing our handcrafted designs.

Feel free to take a look whenever you have a moment!

Best,

Product Zone International
Email: {{sender_email}}`
  },
  {
    id: 'tpl-artisan-showcase',
    name: 'Version 5: Artisan Line Showcase',
    badge: 'Artisan Line',
    subject: 'Handcrafted {{product}} & metal decor for {{company}}',
    body: `Hi there,

Hope you're doing well!

We specialize in making handcrafted metal {{product}}, lanterns, and home accent pieces.

I wanted to share our 2026 collection with you, so I've attached our product catalog for {{company}} to review.

Let me know if any of our pieces catch your eye!

Best regards,

Product Zone International
Email: {{sender_email}}`
  },
  {
    id: 'tpl-brief-intro',
    name: 'Version 6: Brief Introduction',
    badge: 'Brief Intro',
    subject: 'Introducing our {{product}} collection to {{company}}',
    body: `Hi there,

Hope all is well with you!

I'm reaching out from Product Zone International to introduce our handcrafted {{product}} and tabletop decor collection to {{company}}.

Please find our 2026 catalog attached for your reference.

Thank you for your time, and hope you like our collection!

Best regards,

Product Zone International
Email: {{sender_email}}`
  }
];


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

export default function CampaignPage({
  leads = [],
  settings = {},
  onSendCampaign,
  isSending,
  setActiveTab
}) {
  const [selectedTemplateId, setSelectedTemplateId] = useState('tpl-catalog-intro');
  const [product, setProduct] = useState('Metal Candle Holders');
  const [subject, setSubject] = useState(B2B_EMAIL_TEMPLATES[0].subject);
  const [message, setMessage] = useState(B2B_EMAIL_TEMPLATES[0].body);
  const [queueNotice, setQueueNotice] = useState(null);
  const [queueStatus, setQueueStatus] = useState('IDLE');

  // Multi-Recipient Selection (Strictly defaults to NEW, UNCONTACTED valid buyers)
  const [selectedEmails, setSelectedEmails] = useState(() => {
    return new Set(
      leads
        .filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced' && !l.last_contacted_at)
        .map(l => (l.email || '').trim().toLowerCase())
        .filter(Boolean)
    );
  });
  const [showRecipientDrawer, setShowRecipientDrawer] = useState(false);

  // PDF Catalog State
  const [catalogPdfName, setCatalogPdfName] = useState("Candle_Holders.pdf");
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);
  const pdfFileInputRef = useRef(null);

  // Synchronize and sanitize default product keyword
  useEffect(() => {
    const kw = settings?.search_keyword;
    if (kw && !kw.toLowerCase().includes('singing') && kw.trim()) {
      setProduct(kw);
    } else {
      setProduct('Metal Candle Holders');
    }
  }, [settings?.search_keyword]);

  // Live SMTP Dispatch Progress State
  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [dispatchProgress, setDispatchProgress] = useState(0);
  const [dispatchStepLogs, setDispatchStepLogs] = useState([]);
  const [dispatchComplete, setDispatchComplete] = useState(false);
  const [dispatchSummary, setDispatchSummary] = useState(null);

  // Keep selectedEmails strictly populated with UNCONTACTED valid leads
  useEffect(() => {
    if (leads && leads.length > 0) {
      const newValidEmails = leads
        .filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced' && !l.last_contacted_at)
        .map(l => (l.email || '').trim().toLowerCase())
        .filter(Boolean);

      setSelectedEmails(prev => {
        // If user already made a custom selection, retain only valid uncontacted ones
        if (prev.size > 0) {
          const validSet = new Set(newValidEmails);
          const retained = new Set([...prev].filter(e => validSet.has(e)));
          return retained.size > 0 ? retained : validSet;
        }
        // Default strictly to all new uncontacted buyers
        return new Set(newValidEmails);
      });
    } else {
      setSelectedEmails(new Set());
    }
  }, [leads]);

  const parseDateToTime = (dateStr, fallback = 0) => {
    if (!dateStr) return fallback;
    if (typeof dateStr === 'number') return dateStr;
    const s = String(dateStr).trim();
    if (s.includes('T') || s.includes('Z')) {
      const t = new Date(s).getTime();
      if (!isNaN(t)) return t;
    }
    const dt = new Date(s);
    return isNaN(dt.getTime()) ? fallback : dt.getTime();
  };

  // Live filtered list of eligible selected buyers (strictly excludes bounced/invalid)
  // Prioritizes unsent/new buyers at the very top of the list
  const deliverableLeads = [...leads]
    .filter(l => l.validation_status !== 'invalid' && l.reply_status !== 'bounced')
    .sort((a, b) => {
      const aSent = Boolean(a.last_contacted_at);
      const bSent = Boolean(b.last_contacted_at);

      // Unsent / New buyers appear at the top
      if (!aSent && bSent) return -1;
      if (aSent && !bSent) return 1;

      // Within the same group, sort newest first
      const timeA = parseDateToTime(a.discovered_at || a.date, 0);
      const timeB = parseDateToTime(b.discovered_at || b.date, 0);
      return timeB - timeA;
    });

  const uncontactedLeads = deliverableLeads.filter(l => !l.last_contacted_at);

  const eligibleLeads = deliverableLeads.filter(l => {
    const em = (l.email || '').trim().toLowerCase();
    return selectedEmails.has(em);
  });

  const toggleLeadSelection = (email) => {
    if (!email) return;
    const em = email.trim().toLowerCase();
    setSelectedEmails(prev => {
      const next = new Set(prev);
      if (next.has(em)) {
        next.delete(em);
      } else {
        next.add(em);
      }
      return next;
    });
  };

  const selectAllDeliverable = () => {
    const allDeliverable = new Set(
      deliverableLeads
        .map(l => (l.email || '').trim().toLowerCase())
        .filter(Boolean)
    );
    setSelectedEmails(allDeliverable);
  };

  const selectNewOnly = () => {
    const newValid = new Set(
      uncontactedLeads
        .map(l => (l.email || '').trim().toLowerCase())
        .filter(Boolean)
    );
    setSelectedEmails(newValid);
  };

  const deselectAllLeads = () => {
    setSelectedEmails(new Set());
  };

  const handleSelectTemplate = (tpl) => {
    setSelectedTemplateId(tpl.id);
    setSubject(tpl.subject);
    setMessage(tpl.body);
  };

  const handlePdfUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setQueueNotice({ type: 'error', text: 'Please select a valid PDF document (.pdf)' });
      return;
    }

    setIsUploadingPdf(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/presentation/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setCatalogPdfName(data.original_name || file.name);
        setQueueNotice({ type: 'success', text: `Custom export catalog '${file.name}' attached!` });
      } else {
        const err = await res.json().catch(() => ({}));
        setQueueNotice({ type: 'error', text: err.error || 'Upload failed' });
      }
    } catch (err) {
      setQueueNotice({ type: 'error', text: err.message });
    } finally {
      setIsUploadingPdf(false);
    }
  };

  const handleLaunchCampaign = async () => {
    if (eligibleLeads.length === 0) {
      setQueueNotice({
        type: totalLeads > 0 ? 'warning' : 'error',
        text: totalLeads > 0
          ? 'No eligible recipients selected. Please choose target buyers below.'
          : 'Buyer database is empty. Discover buyers in the "Buyers" tab first.'
      });
      return;
    }

    setQueueStatus('RUNNING');
    setDispatchModalOpen(true);
    setDispatchProgress(10);
    setDispatchComplete(false);
    setDispatchStepLogs([
      { text: `Initiating direct catalog outreach to ${eligibleLeads.length} target buyers...`, done: true },
      catalogPdfName 
        ? { text: `Attached Catalog: ${catalogPdfName} (Product Zone Collection).`, done: true }
        : { text: 'Direct outreach without PDF attachment.', done: true }
    ]);

    try {
      const targetIds = eligibleLeads.map(l => l.id);
      
      const report = await onSendCampaign({
        lead_ids: targetIds,
        audience: 'all',
        campaign_mode: 'all',
        subject: subject,
        body: message,
        attach_presentation: Boolean(catalogPdfName),
        force_resend: true,
        include_risky: true,
        include_unvalidated: true
      });

      const successful = report?.successful || [];
      const failed = report?.failed || [];
      const skipped = report?.skipped || [];
      const sentCount = report?.success_count || successful.length;

      eligibleLeads.forEach((buyer, idx) => {
        setTimeout(() => {
          setDispatchProgress(Math.round(((idx + 1) / eligibleLeads.length) * 85) + 15);
          const wasFailed = failed.some(f => f.email === buyer.email);
          setDispatchStepLogs(prev => [
            ...prev,
            { 
              text: wasFailed 
                ? `Failed for ${buyer.company_name || buyer.buyer_name} (${buyer.email})`
                : `Dispatched to ${buyer.company_name || buyer.buyer_name} (${buyer.email}) • ${buyer.country || 'USA/Canada'}`, 
              done: !wasFailed,
              error: wasFailed
            }
          ]);
        }, (idx + 1) * 180);
      });

      setTimeout(() => {
        setDispatchProgress(100);
        setDispatchComplete(true);
        setDispatchSummary({
          initiatedCount: eligibleLeads.length,
          totalSent: sentCount,
          skippedCount: skipped.length,
          failedCount: failed.length,
          catalog: catalogPdfName || 'None',
          mode: 'Live Gmail SMTP'
        });
        setQueueStatus('COMPLETED');
        setQueueNotice({ 
          type: 'success', 
          text: `Dispatched ${sentCount} of ${eligibleLeads.length} emails successfully.` 
        });
      }, (eligibleLeads.length + 1) * 180 + 300);

    } catch (err) {
      setQueueStatus('ERROR');
      setDispatchStepLogs(prev => [...prev, { text: `Dispatch error: ${err.message}`, error: true }]);
      setQueueNotice({ type: 'error', text: 'Dispatch failed: ' + err.message });
    }
  };

  const [previewLeadIndex, setPreviewLeadIndex] = useState(0);

  const activePreviewIndex = Math.min(previewLeadIndex, Math.max(0, eligibleLeads.length - 1));
  const sampleLead = eligibleLeads.length > 0 ? eligibleLeads[activePreviewIndex] : (leads.length > 0 ? leads[0] : {
    buyer_name: 'Sarah',
    company_name: 'Accent Decor',
    email: 'wholesale@accentdecor.com',
    country: 'United States'
  });

  const getCleanBuyerGreetingName = () => 'there';

  const sampleGreetingName = 'there';

  const renderPreviewText = (templateText) => {
    if (!templateText) return '';
    return templateText
      .replaceAll('{{name}}', 'there')
      .replaceAll('{name}', 'there')
      .replaceAll('{{buyer_name}}', 'there')
      .replaceAll('{buyer_name}', 'there')
      .replaceAll('{{company}}', sampleLead.company_name || 'Accent Decor')
      .replaceAll('{company}', sampleLead.company_name || 'Accent Decor')
      .replaceAll('{{company_name}}', sampleLead.company_name || 'Accent Decor')
      .replaceAll('{company_name}', sampleLead.company_name || 'Accent Decor')
      .replaceAll('{{product}}', product || 'Metal Candle Holders')
      .replaceAll('{product}', product || 'Metal Candle Holders')
      .replaceAll('{{country}}', sampleLead.country || 'USA')
      .replaceAll('{country}', sampleLead.country || 'USA')
      .replaceAll('{{sender_email}}', settings?.gmail_email || 'export@productzoneintl.com')
      .replaceAll('{sender_email}', settings?.gmail_email || 'export@productzoneintl.com');
  };

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / CAMPAIGNS"
        title="Export Outreach Campaigns"
        subtitle="Compose and dispatch direct export outreach campaigns to verified B2B buyers."
      />

      <input
        type="file"
        ref={pdfFileInputRef}
        accept=".pdf"
        onChange={handlePdfUpload}
        style={{ display: 'none' }}
      />

      {/* 1. Template Variations Switcher */}
      <div className="app-card" style={{ marginBottom: '16px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="var(--primary)" />
            <h2 className="card-heading" style={{ fontSize: '14px', margin: 0 }}>
              Catalog Showcase Templates (Click to apply)
            </h2>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Switch between different subject lines and pitch styles to showcase your catalog
          </span>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px'
        }}>
          {B2B_EMAIL_TEMPLATES.map((tpl) => {
            const isSelected = selectedTemplateId === tpl.id;
            return (
              <button
                key={tpl.id}
                type="button"
                onClick={() => handleSelectTemplate(tpl)}
                style={{
                  background: isSelected ? 'rgba(59, 130, 246, 0.15)' : '#090e1a',
                  border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: isSelected ? 'var(--primary)' : 'var(--text-muted)',
                    background: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                    padding: '2px 6px',
                    borderRadius: '4px'
                  }}>
                    {tpl.badge}
                  </span>
                  {isSelected && <CheckCircle2 size={12} color="var(--primary)" />}
                </div>
                <div style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  marginTop: '2px'
                }}>
                  {tpl.name}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Main Two-Column Form & Live Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px', alignItems: 'stretch' }}>
        
        {/* Left Column: Form & Targeting */}
        <div className="app-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '20px' }}>
          <div>
            <div className="card-title-badge-row" style={{ marginBottom: '14px' }}>
              <h2 className="card-heading" style={{ fontSize: '15px' }}>Campaign Composer</h2>
              <span className="pill-badge" style={{ fontSize: '10px' }}>
                Product Zone International
              </span>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleLaunchCampaign(); }}>
              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label className="form-label">Product / Export Line</label>
                <input
                  type="text"
                  className="input-field"
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label className="form-label" style={{ marginBottom: '4px' }}>Email Subject</label>
                <input
                  type="text"
                  className="input-field"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label className="form-label" style={{ marginBottom: '4px' }}>Message Body</label>
                <textarea
                  className="input-field"
                  rows={9}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  style={{
                    minHeight: '180px',
                    height: 'auto',
                    resize: 'vertical',
                    lineHeight: '1.6',
                    fontSize: '12px',
                    fontFamily: 'inherit'
                  }}
                />
              </div>

              {/* PDF Catalog Attachment Row */}
              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label className="form-label">Catalog Attachment (PDF)</label>
                {catalogPdfName ? (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: '#0b111e',
                    border: '1px solid rgba(34, 197, 94, 0.4)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
                      <FileText size={14} color="#4ade80" />
                      <span>{catalogPdfName}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--success)', fontWeight: 600 }}>Attached ✓</span>
                      <button
                        type="button"
                        onClick={() => setCatalogPdfName(null)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#f87171',
                          fontSize: '11px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '2px'
                        }}
                      >
                        <Trash2 size={11} />
                        <span>Remove</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div
                    onClick={() => pdfFileInputRef.current?.click()}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: '#0b111e',
                      border: '1px dashed var(--border-color)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
                      <FileText size={14} />
                      <span>Attach custom catalog PDF</span>
                    </div>
                    <button
                      type="button"
                      disabled={isUploadingPdf}
                      style={{
                        background: 'rgba(59, 130, 246, 0.15)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        color: 'var(--primary)',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <Upload size={11} />
                      <span>{isUploadingPdf ? 'Uploading...' : 'Upload PDF'}</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Recipient Targeting Controls */}
              <div style={{
                background: '#070c17',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                      Target Buyers ({eligibleLeads.length})
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowRecipientDrawer(!showRecipientDrawer)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--primary)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Users size={12} />
                    <span>{showRecipientDrawer ? 'Hide List' : 'Inspect Recipients'}</span>
                    {showRecipientDrawer ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </button>
                </div>

                {/* Recipient Drawer */}
                {showRecipientDrawer && (
                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {eligibleLeads.length} of {uncontactedLeads.length} new buyers selected
                      </span>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <button type="button" onClick={selectNewOnly} style={{ background: 'transparent', border: 'none', color: '#4ade80', fontSize: '10.5px', cursor: 'pointer', fontWeight: 600 }}>
                          New Only ({uncontactedLeads.length})
                        </button>
                        <button type="button" onClick={selectAllDeliverable} style={{ background: 'transparent', border: 'none', color: 'var(--primary)', fontSize: '10.5px', cursor: 'pointer' }}>
                          All Valid ({deliverableLeads.length})
                        </button>
                        <button type="button" onClick={deselectAllLeads} style={{ background: 'transparent', border: 'none', color: '#f87171', fontSize: '10.5px', cursor: 'pointer' }}>
                          Clear All
                        </button>
                      </div>
                    </div>

                    <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {deliverableLeads.length === 0 ? (
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', padding: '12px' }}>
                          No deliverable buyers in database. Use Search Buyers to discover new prospects.
                        </div>
                      ) : (
                        deliverableLeads.map(lead => {
                          const em = (lead.email || '').trim().toLowerCase();
                          const isSelected = selectedEmails.has(em);
                          const isContacted = Boolean(lead.last_contacted_at);

                          return (
                            <label
                              key={lead.id || lead.email}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '6px 8px',
                                background: isSelected ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255,255,255,0.02)',
                                borderRadius: '4px',
                                fontSize: '11.5px',
                                cursor: 'pointer'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => toggleLeadSelection(lead.email)}
                                  style={{ accentColor: 'var(--primary)', cursor: 'pointer' }}
                                />
                                <span style={{ color: isSelected ? '#ffffff' : 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  <strong>{lead.company_name || lead.buyer_name}</strong> &middot; <span style={{ fontFamily: 'monospace', color: '#93c5fd' }}>{lead.email}</span>
                                </span>
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '6px', whiteSpace: 'nowrap' }}>
                                {isContacted ? (
                                  <span style={{ fontSize: '9.5px', background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                                    Previously Sent
                                  </span>
                                ) : (
                                  <span style={{ fontSize: '9.5px', background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                                    New Lead ✓
                                  </span>
                                )}
                              </div>
                            </label>
                          );
                        })
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Button */}
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSending || eligibleLeads.length === 0}
                style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
              >
                {isSending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                <span>
                  {isSending 
                    ? 'Dispatching Outreach...' 
                    : `Launch Campaign to ${eligibleLeads.length} Selected Buyers`}
                </span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Dynamic Preview & Delivery Status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', justifyContent: 'space-between' }}>
          
          {/* Sending Queue Card */}
          <div className="app-card" style={{ padding: '16px 20px' }}>
            <div className="queue-header-row" style={{ marginBottom: '10px' }}>
              <h2 className="card-heading" style={{ fontSize: '15px' }}>Outreach Sending Queue</h2>
              <span className="pill-badge">North America Outreach</span>
            </div>

            {queueNotice && (
              <div style={{
                padding: '8px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                marginBottom: '10px',
                backgroundColor: queueNotice.type === 'error' ? 'var(--danger-light)' : queueNotice.type === 'warning' ? 'var(--warning-light)' : 'rgba(59, 130, 246, 0.15)',
                color: queueNotice.type === 'error' ? 'var(--danger)' : queueNotice.type === 'warning' ? 'var(--warning)' : 'var(--primary)',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <AlertCircle size={14} />
                <span>{queueNotice.text}</span>
              </div>
            )}

            <div className="queue-card" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                <h3 className="queue-card-title">
                  Direct Outreach Campaign
                </h3>
                <span className={`badge ${
                  queueStatus === 'RUNNING' ? 'badge-risky' :
                  queueStatus === 'COMPLETED' ? 'badge-valid' : ''
                }`} style={{ fontSize: '10px' }}>
                  {queueStatus}
                </span>
              </div>

              <p className="queue-card-meta" style={{ marginBottom: '8px' }}>
                Ready to dispatch to <strong>{eligibleLeads.length}</strong> target buyers
              </p>

              <div className="queue-actions-row">
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  style={{ marginLeft: 'auto' }}
                  onClick={handleLaunchCampaign}
                  disabled={isSending || eligibleLeads.length === 0}
                >
                  {isSending && queueStatus === 'RUNNING' ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Play size={12} />
                  )}
                  <span>{queueStatus === 'RUNNING' ? 'Dispatching...' : `Dispatch (${eligibleLeads.length})`}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Rendered Live Email Preview */}
          <div className="app-card" style={{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            justifyContent: 'space-between',
            padding: '16px 20px'
          }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', paddingBottom: '8px', borderBottom: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '8px' }}>
                <div className="card-title-badge-row" style={{ margin: 0 }}>
                  <Mail size={15} color="var(--primary)" />
                  <h2 className="card-heading" style={{ fontSize: '14px' }}>Live Rendered Email Preview</h2>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {eligibleLeads.length > 1 && (
                    <select
                      value={activePreviewIndex}
                      onChange={(e) => setPreviewLeadIndex(Number(e.target.value))}
                      style={{
                        background: '#090e1a',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-main)',
                        fontSize: '11px',
                        borderRadius: '4px',
                        padding: '3px 8px',
                        outline: 'none',
                        cursor: 'pointer'
                      }}
                      title="Switch recipient to preview personalized email"
                    >
                      {eligibleLeads.map((lead, idx) => (
                        <option key={lead.email || idx} value={idx}>
                          Preview {idx + 1}/{eligibleLeads.length}: {lead.company_name} (Hi there)
                        </option>
                      ))}
                    </select>
                  )}

                  <span className="badge badge-valid" style={{ fontSize: '10px' }}>
                    To: {sampleLead.email}
                  </span>
                </div>
              </div>

              {/* Subject */}
              <div style={{
                fontSize: '12px',
                fontWeight: 600,
                color: '#ffffff',
                marginBottom: '10px',
                padding: '8px 10px',
                background: '#0d1525',
                borderRadius: '6px',
                border: '1px solid var(--border-color)'
              }}>
                <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>Subject: </span>
                {renderPreviewText(subject)}
              </div>

              {/* Body */}
              <div style={{
                fontSize: '12px',
                color: '#cbd5e1',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.6',
                background: '#070b14',
                padding: '12px 14px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                minHeight: '180px',
                maxHeight: '240px',
                overflowY: 'auto'
              }}>
                {renderPreviewText(message)}
              </div>
            </div>

            {/* Catalog Attached Pill */}
            {catalogPdfName && (
              <div style={{
                marginTop: '10px',
                padding: '8px 12px',
                background: '#0d1525',
                borderRadius: '6px',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '11px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--primary)' }}>
                  <FileText size={13} />
                  <span>{catalogPdfName} (Catalog Attached)</span>
                </div>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Ready</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* Live Outreach Dispatch Progress Modal */}
      {/* ========================================================================= */}
      {dispatchModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'linear-gradient(180deg, #111827 0%, #0b0f19 100%)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '12px',
            width: '100%',
            maxWidth: '580px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(59, 130, 246, 0.2)',
            padding: '24px',
            position: 'relative'
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(59, 130, 246, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Zap size={18} color="#60a5fa" />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                    {dispatchComplete ? 'Campaign Dispatch Complete' : 'Dispatching Campaign'}
                  </h3>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    Live Gmail SMTP Delivery
                  </div>
                </div>
              </div>

              {dispatchComplete && (
                <button
                  type="button"
                  onClick={() => setDispatchModalOpen(false)}
                  style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                >
                  <X size={18} />
                </button>
              )}
            </div>

            {/* Progress Bar */}
            <div style={{ marginBottom: '18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px', color: '#cbd5e1' }}>
                <span>Delivery Progress</span>
                <span style={{ fontWeight: 700, color: '#60a5fa' }}>{dispatchProgress}%</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: '#1f2937', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{
                  width: `${dispatchProgress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%)',
                  borderRadius: '999px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>

            {/* Console Log Ticker */}
            <div style={{
              background: '#070a12',
              borderRadius: '8px',
              border: '1px solid #1e293b',
              padding: '12px 14px',
              maxHeight: '160px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              marginBottom: '18px',
              fontFamily: 'monospace',
              fontSize: '12px'
            }}>
              {dispatchStepLogs.map((log, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', color: log.error ? '#f87171' : '#93c5fd' }}>
                  <span style={{ color: log.error ? '#ef4444' : '#22c55e', fontWeight: 700 }}>✓</span>
                  <span>{log.text}</span>
                </div>
              ))}
              {!dispatchComplete && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '11px' }}>
                  <Loader2 size={12} className="animate-spin" />
                  <span>Sending emails to target mailboxes...</span>
                </div>
              )}
            </div>

            {/* Summary Box when complete */}
            {dispatchComplete && dispatchSummary && (
              <div style={{
                background: 'rgba(34, 197, 94, 0.1)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: '8px',
                padding: '12px 16px',
                marginBottom: '18px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ color: '#4ade80', fontWeight: 700, fontSize: '13px' }}>
                    {dispatchSummary.totalSent} of {dispatchSummary.initiatedCount} Target Outreach Emails Dispatched
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '2px' }}>
                    {dispatchSummary.mode}
                  </div>
                </div>
                <CheckCircle2 size={24} color="#22c55e" />
              </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  downloadFile('/api/export/sent_log?range=today&format=csv', 'sent_log_today.csv');
                }}
                disabled={!dispatchComplete}
              >
                <Download size={13} />
                <span>Download Sent Log (CSV)</span>
              </button>

              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => {
                  setDispatchModalOpen(false);
                  if (setActiveTab) setActiveTab('reports');
                }}
                disabled={!dispatchComplete}
              >
                <span>View Reports &rarr;</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
