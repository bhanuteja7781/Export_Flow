import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ToastContainer from './components/ToastContainer';
import DashboardPage from './pages/DashboardPage';
import LeadsPage from './pages/LeadsPage';
import CampaignPage from './pages/CampaignPage';
import InboxPage from './pages/InboxPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';


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

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const [leads, setLeads] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [settings, setSettings] = useState({});

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isPurging, setIsPurging] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isScanningInbox, setIsScanningInbox] = useState(false);

  const [toasts, setToasts] = useState([]);

  const addToast = (title, message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 9);
    const newToast = { id, title, message, type };
    setToasts([newToast]);
    setTimeout(() => {
      removeToast(id);
    }, 2500);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Fetch initial data from Flask API
  const fetchData = async () => {
    setIsRefreshing(true);
    try {
      const [leadsRes, metricsRes, settingsRes] = await Promise.all([
        fetch('/api/leads'),
        fetch('/api/metrics'),
        fetch('/api/settings')
      ]);

      if (leadsRes.ok) {
        const data = await leadsRes.json();
        setLeads(data.leads || []);
      }
      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data || {});
      }
      if (settingsRes.ok) {
        const data = await settingsRes.json();
        if (data && (!data.search_keyword || data.search_keyword.toLowerCase().includes('singing'))) {
          data.search_keyword = 'Metal Candle Holders';
        }
        setSettings(data || {});
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // 1. Search Leads (Real Live Crawler + Directory)
  const handleSearch = async (arg1, arg2, arg3, arg4 = {}) => {
    setIsSearching(true);
    let keyword = 'Metal Candle Holders';
    let sources = null;
    let maxResults = 8;
    let mode = 'all';
    let country = 'America & Canada';
    let priceSegment = 'all';
    let targetDomains = '';

    if (typeof arg1 === 'object' && arg1 !== null) {
      keyword = arg1.keyword || 'Metal Candle Holders';
      sources = arg1.sources || null;
      maxResults = Number(arg1.limit || arg1.max_results || arg1.maxResults || 8);
      mode = arg1.source || arg1.discoveryMode || arg1.discovery_mode || 'all';
      country = arg1.country || 'America & Canada';
      priceSegment = arg1.price_segment || arg1.priceSegment || 'all';
      targetDomains = arg1.target_domains || arg1.targetDomains || '';
    } else {
      keyword = typeof arg1 === 'string' && arg1.trim() ? arg1 : 'Metal Candle Holders';
      sources = arg2 || null;
      maxResults = Number(arg3 || 8);
      mode = arg4.discoveryMode || arg4.discovery_mode || arg4.source || 'all';
      country = arg4.country || 'America & Canada';
      priceSegment = arg4.price_segment || arg4.priceSegment || 'all';
      targetDomains = arg4.targetDomains || arg4.target_domains || '';
    }

    try {
      const res = await fetch('/api/leads/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword,
          sources,
          max_results: maxResults,
          discovery_mode: mode,
          country: country,
          buyer_type: typeof arg1 === 'object' ? (arg1.buyer_type || 'all') : 'all',
          price_segment: priceSegment,
          target_domains: targetDomains
        })
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Search Complete',
          `Discovered ${data.discovered || 0} buyers (${data.newly_added || 0} brand new).`,
          'success'
        );
        return data;
      } else {
        addToast('Search Failed', 'Failed to retrieve results.', 'error');
        return null;
      }
    } catch (err) {
      console.error('Search failed:', err);
      addToast('Search Error', err.message || 'Network error.', 'error');
      return null;
    } finally {
      setIsSearching(false);
    }
  };

  // 2. Validate Leads
  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const res = await fetch('/api/leads/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Validation Complete',
          `Verified ${data.total_validated || 0} leads (${data.valid_count || 0} deliverable).`,
          'success'
        );
      } else {
        addToast('Validation Failed', 'Could not complete email verification.', 'error');
      }
    } catch (err) {
      console.error('Validation failed:', err);
      addToast('Validation Error', err.message, 'error');
    } finally {
      setIsValidating(false);
    }
  };

  // 3. Classify Leads
  const handleClassify = async (keyword) => {
    setIsClassifying(true);
    try {
      const res = await fetch('/api/leads/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_niche: keyword })
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Classification Complete',
          `Categorized ${data.total_classified || 0} leads into commercial buyer profiles.`,
          'success'
        );
      } else {
        addToast('Classification Notice', 'Fallback heuristics applied.', 'warning');
      }
    } catch (err) {
      console.error('Classification failed:', err);
      addToast('Classification Error', err.message, 'error');
    } finally {
      setIsClassifying(false);
    }
  };

  // 4. Send Campaign
  const handleSendCampaign = async (campaignConfig) => {
    setIsSending(true);
    try {
      const res = await fetch('/api/campaign/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignConfig)
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        const report = data.report || {};
        addToast(
          'Campaign Dispatched',
          `Sent to ${report.success_count || 0} recipients.`,
          'success'
        );
        return report;
      } else {
        const errData = await res.json().catch(() => ({}));
        addToast('Dispatch Error', errData.error || 'Failed to dispatch.', 'error');
      }
    } catch (err) {
      console.error('Campaign send failed:', err);
      addToast('Campaign Error', err.message, 'error');
    } finally {
      setIsSending(false);
    }
  };

  // 5. Scan Inbox for Replies
  const handleScanInbox = async () => {
    setIsScanningInbox(true);
    try {
      const res = await fetch('/api/inbox/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Inbox Scan Complete',
          `Detected ${data.stats?.replies_detected || 0} incoming replies (${data.stats?.mode || 'LIVE'}).`,
          'success'
        );
      } else {
        addToast('Scan Failed', 'Could not fetch incoming replies.', 'error');
      }
    } catch (err) {
      console.error('Inbox scan failed:', err);
      addToast('Inbox Error', err.message, 'error');
    } finally {
      setIsScanningInbox(false);
    }
  };

  // 6. Update Lead
  const handleUpdateLead = async (leadData) => {
    try {
      const res = await fetch('/api/leads/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(leadData)
      });
      if (res.ok) {
        await fetchData();
        addToast('Lead Updated', 'Status updated successfully.', 'success');
      }
    } catch (err) {
      console.error('Failed to update lead:', err);
      addToast('Update Failed', err.message, 'error');
    }
  };

  // 7. Delete Lead & Exclude Domain
  const handleDeleteLead = async (leadIdOrEmail) => {
    try {
      const res = await fetch('/api/leads/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leadIdOrEmail, email: leadIdOrEmail })
      });
      if (res.ok) {
        await fetchData();
        addToast('Lead Deleted', 'Lead removed and domain blacklisted from future search.', 'success');
      } else {
        addToast('Delete Failed', 'Could not delete lead.', 'error');
      }
    } catch (err) {
      console.error('Failed to delete lead:', err);
      addToast('Delete Error', err.message, 'error');
    }
  };

  // 8. Purge Failed / Bounced Leads
  const handlePurgeFailed = async () => {
    setIsPurging(true);
    try {
      const res = await fetch('/api/leads/purge_failed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Purge Complete',
          `Purged ${data.purged_count || 0} failed/bounced buyer records from database.`,
          'success'
        );
      } else {
        addToast('Purge Failed', 'Could not purge failed leads.', 'error');
      }
    } catch (err) {
      console.error('Failed to purge leads:', err);
      addToast('Purge Error', err.message, 'error');
    } finally {
      setIsPurging(false);
    }
  };

  // 9. Recheck Mail & Purge Bad Address Buyers from Report
  const handleRecheckAndClean = async () => {
    setIsScanningInbox(true);
    try {
      const res = await fetch('/api/inbox/recheck_and_clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (res.ok) {
        const data = await res.json();
        await fetchData();
        addToast(
          'Mailbox Rechecked & Cleaned',
          data.message || `Recheck complete: ${data.bounces_purged || 0} invalid address buyers removed from report.`,
          data.bounces_purged > 0 ? 'warning' : 'success'
        );
        return data;
      } else {
        addToast('Recheck Failed', 'Could not recheck mailbox.', 'error');
      }
    } catch (err) {
      console.error('Recheck failed:', err);
      addToast('Recheck Error', err.message, 'error');
    } finally {
      setIsScanningInbox(false);
    }
  };

  // Save Settings
  const handleSaveSettings = async (newSettings) => {
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });
      if (res.ok) {
        await fetchData();
        addToast('Saved', 'Configuration updated.', 'success');
      }
    } catch (err) {
      addToast('Error', 'Failed to save settings.', 'error');
    }
  };

  const handleDownloadCSV = () => {
    downloadFile('/api/export/buyers?format=csv', 'buyers.csv');
  };

  const handleDownloadPDF = () => {
    downloadFile('/api/export/presentation', 'Candle_Holders.pdf');
  };

  return (
    <div className="app-layout">
      {/* Left Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Screen Content */}
      <main className="app-main">
        {activeTab === 'overview' && (
          <DashboardPage
            metrics={metrics}
            leads={leads}
            settings={settings}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'leads' && (
          <LeadsPage
            leads={leads}
            onSearch={handleSearch}
            onValidate={handleValidate}
            onUpdateLead={handleUpdateLead}
            onDeleteLead={handleDeleteLead}
            onPurgeFailed={handlePurgeFailed}
            onRecheckAndClean={handleRecheckAndClean}
            isPurging={isPurging}
            isRechecking={isScanningInbox}
            onDownloadCSV={handleDownloadCSV}
            isSearching={isSearching}
            isValidating={isValidating}
            currentKeyword={settings.search_keyword}
            settings={settings}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'campaigns' && (
          <CampaignPage
            leads={leads}
            settings={settings}
            onSendCampaign={handleSendCampaign}
            isSending={isSending}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'inbox' && (
          <InboxPage
            leads={leads}
            onScanInbox={handleScanInbox}
            onRecheckAndClean={handleRecheckAndClean}
            isScanning={isScanningInbox}
            isRechecking={isScanningInbox}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsPage
            metrics={metrics}
            leads={leads}
          />
        )}

        {activeTab === 'reports' && (
          <ReportsPage
            onDownloadCSV={handleDownloadCSV}
            onDownloadPDF={handleDownloadPDF}
            onUpdateLead={handleUpdateLead}
            onRecheckAndClean={handleRecheckAndClean}
            isRechecking={isScanningInbox}
            metrics={metrics}
            leads={leads}
            settings={settings}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsPage
            initialSettings={settings}
            onSaveSettings={handleSaveSettings}
          />
        )}
      </main>

      {/* Clean Toast Notifications */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  );
}
