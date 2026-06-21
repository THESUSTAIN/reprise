import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = () => {
  return (
    <div className="min-h-screen zy-page-bg text-foreground relative zy-themed">
      {/* Fixed full-height sidebar (96px wide, glued to left edge) */}
      <Sidebar />

      {/* Main column — offset by the sidebar width (96px = 6rem) */}
      <div className="ml-[96px]">
        <Header />
        <main className="px-5 pt-6 pb-12 max-w-[1500px]">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
