import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Eye,
  LineChart,
  HeartPulse,
  Briefcase,
  TrendingUp,
  Plug,
  Globe,
  ShieldCheck,
  SlidersHorizontal,
  Gem,
} from 'lucide-react';
import { navItems } from '../mock/mockData';
import { useAuth } from '../contexts/AuthContext';
import Logo from './Logo';

const iconMap = {
  LayoutDashboard,
  Eye,
  LineChart,
  HeartPulse,
  Briefcase,
  TrendingUp,
  Plug,
  Globe,
  ShieldCheck,
  SlidersHorizontal,
};

const Sidebar = () => {
  const { user } = useAuth();
  const isAdmin = !!user?.is_admin;
  const items = navItems.filter((it) => !it.adminOnly || isAdmin);

  return (
    <aside
      data-testid="sidebar-root"
      className="fixed inset-y-0 left-0 w-[96px] z-30 flex flex-col justify-between items-center bg-gradient-to-b from-[#2a4a8e] via-[#1f3b73] to-[#0f1e50]"
    >
      {/* TOP : Logo officiel MyExtension-ai (icône seule) */}
      <div className="w-full flex items-center justify-center px-2 py-5" data-testid="sidebar-logo">
        <Logo variant="onDark" size="lg" showWordmark={false} />
      </div>

      {/* MIDDLE : icônes de navigation (sidebar navy uniforme — style final-main) */}
      <div className="w-full flex-1 flex items-center px-3">
        <ul className="relative z-10 w-full flex flex-col gap-2 items-center">
          {items.map((item) => {
            const Icon = iconMap[item.icon] || LayoutDashboard;
            return (
              <li key={item.id} className="w-full flex justify-center">
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  data-testid={`sidebar-link-${item.id}`}
                  className={({ isActive }) =>
                    `group relative w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 ${
                      isActive
                        ? 'bg-white/95 shadow-md'
                        : 'hover:bg-white/10 border border-transparent'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon
                        className={`w-[18px] h-[18px] ${
                          isActive ? 'text-[#1f3b73]' : 'text-white/75 group-hover:text-white'
                        }`}
                        strokeWidth={1.9}
                      />
                      <span className="pointer-events-none absolute left-[60px] top-1/2 -translate-y-1/2 whitespace-nowrap rounded-md bg-[#0f1e50] text-white text-xs px-2.5 py-1.5 opacity-0 group-hover:opacity-100 transition-opacity border border-white/10 shadow-xl z-50">
                        {item.label}
                      </span>
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </div>

      {/* BOTTOM : Gem upgrade button */}
      <div className="w-full flex items-center justify-center px-2 py-4">
        <button
          data-testid="sidebar-upgrade-btn"
          className="w-10 h-10 rounded-full bg-gradient-to-br from-[#d4b78c] to-[#c4a374] flex items-center justify-center shadow-lg hover:scale-105 transition-transform"
          title="Upgrade Plan"
        >
          <Gem className="w-[18px] h-[18px] text-[#0f1e50]" strokeWidth={2} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
