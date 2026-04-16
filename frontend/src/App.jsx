import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ClerkProvider, SignIn, SignUp } from '@clerk/clerk-react';
import MainLayout from './layout/MainLayout';
import CallLogs from './pages/CallLogs';
import VoiceBotSetup from './pages/VoiceBotSetup';
import DocumentUploadPage from './pages/DocumentUploadPage';
import Settings from './pages/Settings';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

// Import your publishable key
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

function App() {
  if (!clerkPubKey) {
    return <div>Please add your VITE_CLERK_PUBLISHABLE_KEY to your .env file</div>;
  }

  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <Router>
        <Routes>
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/sign-up" element={<SignUp />} />
          <Route path="/" element={<MainLayout />}>
            <Route index element={<ProtectedRoute><CallLogs /></ProtectedRoute>} />
            <Route path="call-logs" element={<ProtectedRoute><CallLogs /></ProtectedRoute>} />
            <Route path="voice-bot-setup" element={<ProtectedRoute><VoiceBotSetup /></ProtectedRoute>} />
            <Route path="document-upload" element={<ProtectedRoute><DocumentUploadPage /></ProtectedRoute>} />
            <Route path="settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          </Route>
        </Routes>
      </Router>
    </ClerkProvider>
  );
}

export default App;
