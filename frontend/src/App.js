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
                element={
                  <StubPage
                    title="Connexion"
                    description="Accédez à votre cockpit MyExtension-ai"
                    testId="page-login"
                    sourceFile="final-main/frontend/src/pages/Login.js"
                    status="porting"
                  />
                }
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
                <Route path="/parametres" element={<Settings />} />
                <Route path="/settings" element={<Navigate to="/parametres" replace />} />

                <Route
                  path="/pilotage"
                  element={
                    <StubPage
                      title="Pilotage financier"
                      description="CA, trésorerie, salaire possible — votre clarté financière en temps réel"
                      testId="page-pilotage"
                      sourceFile="final-main/frontend/src/pages/Pilotage.js"
                      status="porting"
                    />
                  }
                />
                <Route
                  path="/bien-etre"
                  element={
                    <StubPage
                      title="Bien-être"
                      description="Check-in énergie quotidien, prévention burn-out, carnet de bord"
                      testId="page-bienetre"
                      sourceFile="final-main/frontend/src/pages/BienEtre.js"
                      status="porting"
                    />
                  }
                />
                <Route
                  path="/espace"
                  element={
                    <StubPage
                      title="Espace de travail"
                      description="Missions, documents IA, processus métier — votre Co-pilote au quotidien"
                      testId="page-espace"
                      sourceFile="final-main/frontend/src/pages/EspaceDeTravail.js"
                      status="porting"
                    />
                  }
                />
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
