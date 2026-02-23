import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

import Dashboard from './components/Dashboard';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [monitoring, setMonitoring] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  return (
    <Router>
      <div className="App">
        <Sidebar />
        <div className="main-content">
          <Header 
            darkMode={darkMode} 
            setDarkMode={setDarkMode}
            monitoring={monitoring}
          />
          <Routes>
            <Route path="/" element={
              <Dashboard 
                monitoring={monitoring} 
                setMonitoring={setMonitoring} 
              />
            } />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
        <ToastContainer position="top-right" theme={darkMode ? "dark" : "light"} />
      </div>
    </Router>
  );
}

export default App;