import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';

import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import VisionBoardPage from './pages/VisionBoardPage';
import Settings from './pages/Settings';
import Login from './pages/Login';
import FmShell from '@fm/FmShell';
import FmPilotage from '@fm/pages/Pilotage';
import FmBienEtre from '@fm/pages/BienEtre';
import FmEspace from '@fm/pages/EspaceDeTravail';
import StubPage from './pages/StubPage';

/**
 * Routes Zayado MyExtension-ai
 *
 * Layout (reprise) = Sidebar + Header + Outlet
 * Pages live (reprise) : Dashboard, VisionBoard, Settings/Paramètres
 * Pages stub (à porter depuis final-main) : Pilotage, Bien-être,
 *   Espace, Croissance, Onboarding, Login, Admin, Integrations, WordPress
 */
function App() {
  return (
    <div className="App" data-testid="app-root">
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Toaster position="top-right" richColors closeButton />
            <Routes>
              {/* Routes publiques sans Layout */}
              <Route
                path="/login"
                element={<Login />}
              />
              <Route
                path="/onboarding"
                element={
                  <StubPage
                    title="Onboarding"
                    description="Configuration de votre cockpit en 5 minutes"
                    testId="page-onboarding"
                    sourceFile="final-main/frontend/src/pages/Onboarding.js"
                    status="porting"
                  />
                }
              />

              {/* Vision Board — page autonome (sa propre top-nav, sans Layout global) */}
              <Route path="/vision-board" element={<VisionBoardPage />} />

              {/* Routes app avec Layout (Sidebar + Header) */}
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                {/* Contenu final-main inséré DANS la coquille reprise (Header + Sidebar) */}
                <Route path="/pilotage" element={<FmShell><FmPilotage /></FmShell>} />
                <Route path="/bien-etre" element={<FmShell><FmBienEtre /></FmShell>} />
                <Route path="/espace" element={<FmShell><FmEspace /></FmShell>} />
                <Route path="/parametres" element={<Settings />} />
                <Route path="/settings" element={<Navigate to="/parametres" replace />} />

                <Route
                  path="/croissance"
                  element={
                    <StubPage
                      title="Croissance"
                      description="Leads détectés, pipeline, Expansion Agent — votre acquisition pilotée"
                      testId="page-croissance"
                      sourceFile="final-main/frontend/src/pages/Croissance.js"
                      status="porting"
                    />
                  }
                />
                <Route
                  path="/integrations"
                  element={
                    <StubPage
                      title="Intégrations"
                      description="Google Drive, OneDrive, Notion, Trello — connectez vos outils"
                      testId="page-integrations"
                      sourceFile="final-main/frontend/src/pages/Integrations.js"
                      status="porting"
                    />
                  }
                />
                <Route
                  path="/wordpress"
                  element={
                    <StubPage
                      title="WordPress"
                      description="Pilotez votre site Zayado.net depuis le cockpit (admin)"
                      testId="page-wordpress"
                      sourceFile="final-main/frontend/src/pages/WordPress.js"
                      status="porting"
                    />
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <StubPage
                      title="Administration"
                      description="Gestion utilisateurs, content OS, paramètres système"
                      testId="page-admin"
                      sourceFile="final-main/frontend/src/pages/Admin.js"
                      status="porting"
                    />
                  }
                />
              </Route>

              {/* Catch-all → Dashboard */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </div>
  );
}

export default App;
