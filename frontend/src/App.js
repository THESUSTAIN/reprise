import "@/App.css";
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider, useApp } from "@/context/AppContext";
import { Toaster } from "@/components/ui/sonner";
import AppLayout from "@/components/layout/AppLayout";
import Login from "@/pages/Login";
import Cockpit from "@/pages/Cockpit";
import Copilote from "@/pages/Copilote";
import Vision from "@/pages/Vision";
import Croissance from "@/pages/Croissance";
import Pilotage from "@/pages/Pilotage";
import BienEtre from "@/pages/BienEtre";
import Contexte from "@/pages/Contexte";
import Mindset from "@/pages/Mindset";
import VisionBoard from "@/pages/VisionBoard";
import Agenda from "@/pages/Agenda";
import Parametres from "@/pages/Parametres";

function Protected({ children }) {
  const { authed } = useApp();
  if (!authed) return <Navigate to="/" replace />;
  return children;
}

function Shell() {
  const { authed } = useApp();
  return (
    <Routes>
      <Route path="/" element={authed ? <Navigate to="/cockpit" replace /> : <Login />} />
      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route path="/cockpit" element={<Cockpit />} />
        <Route path="/copilote" element={<Copilote />} />
        <Route path="/vision" element={<Vision />} />
        <Route path="/croissance" element={<Croissance />} />
        <Route path="/pilotage" element={<Pilotage />} />
        <Route path="/bien-etre" element={<BienEtre />} />
        <Route path="/contexte" element={<Contexte />} />
        <Route path="/mindset" element={<Mindset />} />
        <Route path="/vision-board" element={<VisionBoard />} />
        <Route path="/agenda" element={<Agenda />} />
        <Route path="/parametres" element={<Parametres />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Shell />
        <Toaster position="bottom-right" richColors />
      </BrowserRouter>
    </AppProvider>
  );
}
