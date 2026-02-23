import React, { useState } from 'react';
import { toast } from 'react-toastify';
import './Settings.css';

const Settings = () => {
  const [credentials, setCredentials] = useState({
    vfsEmail: '',
    vfsPassword: '',
    telegramToken: '',
    telegramChatId: ''
  });

  const [browserSettings, setBrowserSettings] = useState({
    headless: false,
    antiDetection: true,
    sessionPersistence: true
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setBrowserSettings(prev => ({ ...prev, [name]: checked }));
  };

  const saveSettings = () => {
    // API call would go here
    toast.success('✅ Ayarlar kaydedildi!');
  };

  const testTelegram = () => {
    if (!credentials.telegramToken || !credentials.telegramChatId) {
      toast.error('Telegram bilgileri eksik!');
      return;
    }
    // API call would go here
    toast.info('📱 Telegram test mesajı gönderiliyor...');
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>Ayarlar</h1>
        <p className="subtitle">Sistem konfigürasyonu ve tercihler</p>
      </div>

      {/* VFS Credentials */}
      <div className="settings-section card">
        <h2>VFS Global Bilgileri</h2>
        <div className="form-group">
          <label>VFS Email</label>
          <input
            type="email"
            name="vfsEmail"
            value={credentials.vfsEmail}
            onChange={handleInputChange}
            placeholder="ornek@email.com"
            className="input-field"
          />
        </div>
        <div className="form-group">
          <label>VFS Şifre</label>
          <input
            type="password"
            name="vfsPassword"
            value={credentials.vfsPassword}
            onChange={handleInputChange}
            placeholder="••••••••"
            className="input-field"
          />
        </div>
      </div>

      {/* Telegram Settings */}
      <div className="settings-section card">
        <h2>Telegram Bot Ayarları</h2>
        <div className="form-group">
          <label>Bot Token</label>
          <input
            type="text"
            name="telegramToken"
            value={credentials.telegramToken}
            onChange={handleInputChange}
            placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            className="input-field"
          />
        </div>
        <div className="form-group">
          <label>Chat ID</label>
          <input
            type="text"
            name="telegramChatId"
            value={credentials.telegramChatId}
            onChange={handleInputChange}
            placeholder="123456789"
            className="input-field"
          />
        </div>
        <button onClick={testTelegram} className="btn btn-secondary">
          📱 Test Mesajı Gönder
        </button>
      </div>

      {/* Browser Settings */}
      <div className="settings-section card">
        <h2>Tarayıcı Ayarları</h2>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="headless"
              checked={browserSettings.headless}
              onChange={handleCheckboxChange}
            />
            <span>Headless Mode (Arka planda çalış)</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="antiDetection"
              checked={browserSettings.antiDetection}
              onChange={handleCheckboxChange}
            />
            <span>Anti-Detection (Bot koruması bypass)</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="sessionPersistence"
              checked={browserSettings.sessionPersistence}
              onChange={handleCheckboxChange}
            />
            <span>Session Persistence (Oturum kaydet)</span>
          </label>
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="settings-section card">
        <h2>Gelişmiş Ayarlar</h2>
        <div className="info-box">
          <p>⚡ <strong>Anti-Detection:</strong> Bot algılama sistemlerini bypass eder</p>
          <p>🔄 <strong>Session Persistence:</strong> Oturumları kaydetip tekrar kullanır</p>
          <p>🖥️ <strong>Headless Mode:</strong> Tarayıcı görünmez modda çalışır</p>
        </div>
      </div>

      {/* Save Button */}
      <div className="settings-actions">
        <button onClick={saveSettings} className="btn btn-primary">
          💾 Ayarları Kaydet
        </button>
      </div>
    </div>
  );
};

export default Settings;