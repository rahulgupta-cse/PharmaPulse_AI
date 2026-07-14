import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import LogInteraction from './components/LogInteraction';
import InteractionList from './components/InteractionList';
import HCPList from './components/HCPList';
import HCPDetail from './components/HCPDetail';

function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/log-interaction" element={<LogInteraction />} />
            <Route path="/interactions" element={<InteractionList />} />
            <Route path="/hcps" element={<HCPList />} />
            <Route path="/hcps/:id" element={<HCPDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </main>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1A1A2E',
            color: '#FFFFFF',
            border: '1px solid rgba(108, 99, 255, 0.3)',
            borderRadius: '12px',
            fontFamily: "'Inter', sans-serif",
            fontSize: '14px',
            backdropFilter: 'blur(20px)',
          },
          success: {
            iconTheme: {
              primary: '#00D4AA',
              secondary: '#1A1A2E',
            },
          },
          error: {
            iconTheme: {
              primary: '#FF6B6B',
              secondary: '#1A1A2E',
            },
          },
        }}
      />
    </div>
  );
}

export default App;
