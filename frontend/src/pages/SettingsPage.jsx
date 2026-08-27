import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import { Save, CheckCircle2, Mail, Bot, Sliders, Eye, EyeOff } from 'lucide-react';

export default function SettingsPage({ initialSettings = {}, onSaveSettings }) {
  const getCached = () => {
    try {
      return JSON.parse(localStorage.getItem('exportflow_settings') || '{}');
    } catch {
      return {};
    }
  };
  const cached = getCached();

  const [gmailEmail, setGmailEmail] = useState(initialSettings.gmail_email || cached.gmail_email || '');
  const [appPassword, setAppPassword] = useState(initialSettings.gmail_app_password || initialSettings.app_password || cached.gmail_app_password || cached.app_password || '');
  const [geminiApiKey, setGeminiApiKey] = useState(initialSettings.gemini_api_key || cached.gemini_api_key || '');
  const [searchKeyword, setSearchKeyword] = useState(initialSettings.search_keyword || cached.search_keyword || 'Metal Candle Holders');
  const [sendDelay, setSendDelay] = useState(initialSettings.send_delay ?? initialSettings.send_delay_seconds ?? cached.send_delay ?? 2.5);
  const [dailySendLimit, setDailySendLimit] = useState(initialSettings.daily_send_limit ?? cached.daily_send_limit ?? 100);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    const local = getCached();
    if (initialSettings && Object.keys(initialSettings).length > 0) {
      if (initialSettings.gmail_email) setGmailEmail(initialSettings.gmail_email);
      if (initialSettings.gmail_app_password || initialSettings.app_password) {
        setAppPassword(initialSettings.gmail_app_password || initialSettings.app_password);
      }
      if (initialSettings.gemini_api_key) setGeminiApiKey(initialSettings.gemini_api_key);
      if (initialSettings.search_keyword) setSearchKeyword(initialSettings.search_keyword);
      if (initialSettings.send_delay || initialSettings.send_delay_seconds) {
        setSendDelay(initialSettings.send_delay ?? initialSettings.send_delay_seconds);
      }
      if (initialSettings.daily_send_limit) setDailySendLimit(initialSettings.daily_send_limit);
    } else if (local && Object.keys(local).length > 0) {
      if (local.gmail_email) setGmailEmail(local.gmail_email);
      if (local.gmail_app_password || local.app_password) setAppPassword(local.gmail_app_password || local.app_password);
      if (local.gemini_api_key) setGeminiApiKey(local.gemini_api_key);
      if (local.search_keyword) setSearchKeyword(local.search_keyword);
      if (local.send_delay) setSendDelay(local.send_delay);
      if (local.daily_send_limit) setDailySendLimit(local.daily_send_limit);
    }
  }, [initialSettings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const configToSave = {
      gmail_email: gmailEmail,
      gmail_app_password: appPassword,
      app_password: appPassword,
      gemini_api_key: geminiApiKey,
      search_keyword: searchKeyword,
      send_delay: Number(sendDelay),
      send_delay_seconds: Number(sendDelay),
      daily_send_limit: Number(dailySendLimit)
    };

    try {
      localStorage.setItem('exportflow_settings', JSON.stringify(configToSave));
    } catch (err) {}

    if (onSaveSettings) {
      await onSaveSettings(configToSave);
    }
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="page-container">
      <Header
        breadcrumb="WORKSPACE / SETTINGS"
        title="Settings"
      />

      {savedSuccess && (
        <div style={{
          padding: '12px 16px',
          background: 'var(--success-light)',
          border: '1px solid var(--success-border)',
          borderRadius: '8px',
          color: 'var(--success)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          fontWeight: 600,
          marginBottom: '20px'
        }}>
          <CheckCircle2 size={16} />
          <span>Configuration saved successfully.</span>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          
          {/* Card 1: Gmail SMTP */}
          <div className="app-card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-title-badge-row" style={{ marginBottom: '18px' }}>
              <Mail size={16} color="var(--primary)" />
              <h2 className="card-heading">Gmail SMTP Dispatcher</h2>
            </div>

            <div className="form-group">
              <label className="form-label">Gmail Address</label>
              <input
                type="email"
                className="input-field"
                placeholder="your_email@gmail.com"
                value={gmailEmail}
                onChange={(e) => setGmailEmail(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0 }}>16-Character App Password</label>
                <a
                  href="https://myaccount.google.com/apppasswords"
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    fontSize: '11px',
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontWeight: 500
                  }}
                >
                  Open Google Page &rarr;
                </a>
              </div>

              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? "text" : "password"}
                  className="input-field"
                  placeholder="Enter 16-character App Password"
                  value={appPassword}
                  onChange={(e) => setAppPassword(e.target.value)}
                  style={{ paddingRight: '36px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '9px',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <div style={{
              background: '#070b14',
              borderRadius: '8px',
              padding: '12px 14px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginTop: 'auto',
              border: '1px solid var(--border-subtle)'
            }}>
              <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>
                How to generate your App Password:
              </strong>
              1. Turn 2-Step Verification ON in Google Account.<br />
              2. Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>myaccount.google.com/apppasswords</a>.<br />
              3. Type <strong>ExportFlow</strong> under "App name" and click <strong>Create</strong>.<br />
              4. Copy the 16-letter code and paste it above.
            </div>
          </div>

          {/* Card 2: AI Classification & Niche */}
          <div className="app-card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-title-badge-row" style={{ marginBottom: '18px' }}>
              <Bot size={16} color="var(--primary)" />
              <h2 className="card-heading">AI Classification (Gemini)</h2>
            </div>

            <div className="form-group">
              <label className="form-label">Default Target Keyword</label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g. Metal Candle Holders"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0 }}>Google Gemini API Key</label>
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    fontSize: '11px',
                    color: 'var(--primary)',
                    textDecoration: 'none',
                    fontWeight: 500
                  }}
                >
                  Open AI Studio &rarr;
                </a>
              </div>

              <div style={{ position: 'relative' }}>
                <input
                  type={showApiKey ? "text" : "password"}
                  className="input-field"
                  placeholder="Enter Gemini API Key"
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  style={{ paddingRight: '36px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '9px',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                >
                  {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <div style={{
              background: '#070b14',
              borderRadius: '8px',
              padding: '12px 14px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginTop: 'auto',
              border: '1px solid var(--border-subtle)'
            }}>
              <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>
                How to get your Gemini API key:
              </strong>
              1. Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" style={{ color: 'var(--primary)' }}>aistudio.google.com/app/apikey</a>.<br />
              2. Click the blue <strong>"+ Create API key"</strong> button.<br />
              3. Select your project and copy your key into the field above.
            </div>
          </div>
        </div>

        {/* Card 3: Safeguards & Speed */}
        <div className="app-card">
          <div className="card-title-badge-row" style={{ marginBottom: '18px' }}>
            <Sliders size={16} color="var(--primary)" />
            <h2 className="card-heading">Outreach Safeguards & Rate Limiting</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Daily Send Limit</label>
              <input
                type="number"
                className="input-field"
                value={dailySendLimit}
                onChange={(e) => setDailySendLimit(e.target.value)}
                min="1"
                max="500"
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Prevents account suspension by capping maximum daily dispatches.
              </span>
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Delay Between Sends (sec)</label>
              <input
                type="number"
                step="0.5"
                className="input-field"
                value={sendDelay}
                onChange={(e) => setSendDelay(e.target.value)}
                min="1.0"
                max="30.0"
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Randomized interval between outbound emails for natural sending.
              </span>
            </div>
          </div>
        </div>

        {/* Save Bar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '10px 24px' }}>
            <Save size={15} />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
