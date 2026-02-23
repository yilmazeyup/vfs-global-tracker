import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import './Dashboard.css';

const Dashboard = ({ monitoring, setMonitoring }) => {
  const [stats, setStats] = useState({
    totalScans: 0,
    lastScan: null,
    appointmentsFound: 0,
    activeOffices: []
  });
  
  const [selectedCountry, setSelectedCountry] = useState('netherlands');
  const [selectedOffices, setSelectedOffices] = useState(['ankara', 'istanbul']);
  const [scanInterval, setScanInterval] = useState(300);

  const countries = {
    netherlands: { name: '🇳🇱 Hollanda', offices: ['Ankara', 'İstanbul'] },
    germany: { name: '🇩🇪 Almanya', offices: ['Ankara', 'İstanbul', 'İzmir'] },
    italy: { name: '🇮🇹 İtalya', offices: ['Ankara', 'İstanbul'] },
    norway: { name: '🇳🇴 Norveç', offices: ['Ankara'] },
    canada: { name: '🇨🇦 Kanada', offices: ['Ankara', 'İstanbul'] }
  };

  const startMonitoring = () => {
    if (selectedOffices.length === 0) {
      toast.error('Lütfen en az bir ofis seçin!');
      return;
    }

    setMonitoring(true);
    toast.success('🚀 Randevu taraması başlatıldı!');
    
    // Simulated monitoring update
    const interval = setInterval(() => {
      if (!monitoring) return;
      
      setStats(prev => ({
        ...prev,
        totalScans: prev.totalScans + 1,
        lastScan: new Date().toLocaleTimeString('tr-TR')
      }));
    }, scanInterval * 1000);
  };

  const stopMonitoring = () => {
    setMonitoring(false);
    toast.info('⏹️ Tarama durduruldu');
  };

  const handleOfficeToggle = (office) => {
    setSelectedOffices(prev => 
      prev.includes(office) 
        ? prev.filter(o => o !== office)
        : [...prev, office]
    );
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>VFS Global Randevu Takip Sistemi</h1>
        <p className="subtitle">⚡ Manaliza Enterprise Solutions</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🔍</div>
          <div className="stat-content">
            <h3>{stats.totalScans}</h3>
            <p>Toplam Tarama</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <h3>{stats.lastScan || '--:--'}</h3>
            <p>Son Tarama</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div className="stat-content">
            <h3>{stats.appointmentsFound}</h3>
            <p>Bulunan Randevu</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🏢</div>
          <div className="stat-content">
            <h3>{selectedOffices.length}</h3>
            <p>Aktif Ofis</p>
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="control-panel card">
        <h2>Tarama Ayarları</h2>
        
        <div className="control-group">
          <label>Ülke Seçimi</label>
          <select 
            value={selectedCountry} 
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="select-input"
          >
            {Object.entries(countries).map(([code, country]) => (
              <option key={code} value={code}>{country.name}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Ofis Seçimi</label>
          <div className="office-checkboxes">
            {countries[selectedCountry].offices.map(office => (
              <label key={office} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedOffices.includes(office.toLowerCase())}
                  onChange={() => handleOfficeToggle(office.toLowerCase())}
                />
                <span>{office}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="control-group">
          <label>Tarama Aralığı (saniye)</label>
          <input
            type="number"
            value={scanInterval}
            onChange={(e) => setScanInterval(e.target.value)}
            min="60"
            max="3600"
            className="input-field"
          />
        </div>

        <div className="control-actions">
          {!monitoring ? (
            <button onClick={startMonitoring} className="btn btn-primary">
              🚀 Taramayı Başlat
            </button>
          ) : (
            <button onClick={stopMonitoring} className="btn btn-danger">
              ⏹️ Taramayı Durdur
            </button>
          )}
        </div>
      </div>

      {/* Live Status */}
      {monitoring && (
        <div className="live-status card">
          <div className="live-header">
            <h2>🔴 Canlı Tarama</h2>
            <span className="pulse"></span>
          </div>
          <div className="scanning-animation">
            <div className="scanner"></div>
            <p>Randevular taranıyor...</p>
          </div>
          <div className="scanning-offices">
            {selectedOffices.map(office => (
              <div key={office} className="office-status">
                <span className="office-name">{office.charAt(0).toUpperCase() + office.slice(1)}</span>
                <span className="status-active">● Aktif</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="activity-log card">
        <h2>Son Aktiviteler</h2>
        <div className="activity-list">
          <div className="activity-item">
            <span className="activity-time">{new Date().toLocaleTimeString('tr-TR')}</span>
            <span className="activity-text">Sistem başlatıldı</span>
          </div>
          {monitoring && (
            <div className="activity-item">
              <span className="activity-time">{new Date().toLocaleTimeString('tr-TR')}</span>
              <span className="activity-text">Tarama başladı - {selectedCountry.toUpperCase()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;