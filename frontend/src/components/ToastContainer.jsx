import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function ToastContainer({ toasts = [], onRemoveToast, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;
  const dismiss = onRemoveToast || onDismiss || (() => {});

  return (
    <div className="toast-container">
      {toasts.slice(-2).map((toast) => {
        const isSuccess = toast.type === 'success';
        const isError = toast.type === 'error';

        return (
          <div key={toast.id} className={`toast-item ${toast.type || 'info'}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isSuccess && <CheckCircle2 size={16} color="var(--success)" />}
              {isError && <AlertCircle size={16} color="var(--danger)" />}
              {!isSuccess && !isError && <Info size={16} color="var(--primary)" />}
              <strong className="toast-title" style={{ fontSize: '12px' }}>{toast.title}</strong>
            </div>

            <p className="toast-message" style={{ margin: '4px 0 0 24px', fontSize: '11px' }}>{toast.message}</p>

            <button 
              className="toast-close-btn" 
              onClick={() => dismiss(toast.id)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
