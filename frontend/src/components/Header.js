import React from 'react';
import './Header.css';

const Header = ({ darkMode, setDarkMode, monitoring }) => {
  return (
    <header className="header">
      <div className="header-left">
        <h3>VFS Global Randevu Takip Sistemi</h3>
      </div>
      
      <div className="header-right">
        <div className="status-indicator">
          <span className={`status-dot ${monitoring ? 'active' : 'inactive'}`}></span>
          <span className="status-text">
            {monitoring ? 'Tarama Aktif' : 'Tarama Kapalı'}
          </span>
        </div>
        
        <button 
          className="theme-toggle"
          onClick={() => setDarkMode(!darkMode)}
          title="Tema Değiştir"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
};

export default Header;