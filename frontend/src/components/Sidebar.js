import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/', icon: '📊', label: 'Dashboard' },
    { path: '/settings', icon: '⚙️', label: 'Ayarlar' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>VFS Tracker</h2>
        <span className="version">v1.0.0</span>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="footer-info">
          <p>⚡ Manaliza</p>
          <p className="footer-subtitle">Enterprise Solutions</p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;