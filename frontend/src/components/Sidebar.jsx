import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  TrendingUp, 
  Send, 
  FileText, 
  Settings,
  Globe2,
  Inbox
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'leads', label: 'Buyers', icon: Users },
    { id: 'campaigns', label: 'Campaigns', icon: Send },
    { id: 'inbox', label: 'Inbox & Replies', icon: Inbox },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'reports', label: 'Reports & Catalog', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <aside className="sorter-sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="logo-badge">
          <Globe2 size={18} />
        </div>
        <div className="logo-text-group">
          <span className="logo-title">EXPORTFLOW</span>
          <span className="logo-subtitle">OUTREACH AUTOMATION</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="status-dot" />
        <span>Export Pipeline Live</span>
      </div>
    </aside>
  );
}
