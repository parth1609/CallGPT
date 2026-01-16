import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layout/MainLayout';
import Dashboard from './pages/Dashboard';
import CallLogs from './pages/CallLogs';
import VoiceBotSetup from './pages/VoiceBotSetup';
import FAQs from './pages/FAQs';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="call-logs" element={<CallLogs />} />
          <Route path="voice-bot-setup" element={<VoiceBotSetup />} />
          <Route path="faqs" element={<FAQs />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
