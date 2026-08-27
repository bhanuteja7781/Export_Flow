import React from 'react';

export default function Header({
  breadcrumb = 'WORKSPACE',
  title = ''
}) {
  return (
    <div className="header-banner" style={{ marginBottom: '20px' }}>
      <div>
        <div className="breadcrumb">{breadcrumb}</div>
        <h1 className="header-greeting">{title}</h1>
      </div>
    </div>
  );
}
