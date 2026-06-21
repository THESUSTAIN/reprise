import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@fm/context/AuthContext";

export default function ProtectedRoute({ children, requireOnboarding = true }) {
  const { user, booting } = useAuth();
  const loc = useLocation();

  if (booting) {
    return (
      <div className="min-h-screen canvas-bg grid place-items-center">
        <div className="text-ink-soft text-sm">Chargement…</div>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: loc }} replace />;
  }
  if (requireOnboarding && !user.onboarding_done) {
    return <Navigate to="/onboarding" replace />;
  }
  return children;
}
