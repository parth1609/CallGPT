import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layout/MainLayout';
import CallLogs from './pages/CallLogs';
import VoiceBotSetup from './pages/VoiceBotSetup';
import DocumentUploadPage from './pages/DocumentUploadPage';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<CallLogs />} />
          <Route path="call-logs" element={<CallLogs />} />
          <Route path="voice-bot-setup" element={<VoiceBotSetup />} />
          <Route path="document-upload" element={<DocumentUploadPage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
