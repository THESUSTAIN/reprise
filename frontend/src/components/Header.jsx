import React, { useState } from 'react';
import {
  Search,
  Bell,
  Mail,
  Sun,
  Moon,
  ChevronDown,
  UserPlus,
  CreditCard,
  Sparkles,
  Settings as SettingsIcon,
  LogOut,
  User,
  HelpCircle,
  Grid3x3,
  Home,
  Leaf,
  Store,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { useTheme } from '../contexts/ThemeContext';
import { headerNotifications, headerMessages, userProfile, quickJumpModules } from '../mock/mockData';
import { toast } from 'sonner';
import Logo from './Logo';

const notifIconMap = { UserPlus, CreditCard, Sparkles, Bell };
const quickIconMap = { Home, Leaf, Store };

const Header = () => {
  const { theme, toggleTheme } = useTheme();
  const [search, setSearch] = useState('');

  const unreadNotifs = headerNotifications.filter((n) => n.unread).length;
  const unreadMsgs = headerMessages.filter((m) => m.unread).length;

  return (
    <header className="sticky top-0 z-20" data-testid="header-root">
      <div className="zy-header-band rounded-b-2xl flex items-center h-[64px] relative mx-5 md:mx-10">
        {/* Scoop top-left — concave corner where header meets page bg (LEFT side) */}
        <svg
          className="absolute left-[-30px] top-0 rotate-90 pointer-events-none zy-header-scoop"
          width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path d="M30 0H0V30C0 13.431 13.431 0 30 0Z" />
        </svg>
        {/* Scoop top-right — concave corner on the right */}
        <svg
          className="absolute right-[-30px] top-0 pointer-events-none zy-header-scoop"
          width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path d="M30 0H0V30C0 13.431 13.431 0 30 0Z" />
        </svg>

        {/* Wordmark "MyExtension-ai by Zayado" — sur bande navy → toujours variante claire */}
        <div className="hidden md:flex items-center pl-5 pr-4 select-none" data-testid="header-wordmark">
          <Logo variant="onDark" size="md" />
          <span className="w-px h-7 bg-white/15 ml-3" />
        </div>

        {/* Search */}
        <div className="flex-1 max-w-[380px] px-4">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[15px] h-[15px] text-current opacity-60" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher..."
              className="zy-search w-full h-10 pl-10 pr-4 rounded-lg text-sm transition"
            />
          </div>
        </div>

        {/* Spacer where the gradient is visible */}
        <div className="flex-1" />

        {/* Right zone: action buttons sitting on the gradient */}
        <div className="flex items-center gap-2 pr-4 relative z-10">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            data-testid="header-theme-toggle"
            className="w-9 h-9 rounded-lg bg-white/12 hover:bg-white/20 border border-white/15 flex items-center justify-center transition"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-[15px] h-[15px] text-[#f3d8a6]" />
            ) : (
              <Moon className="w-[15px] h-[15px] text-white" />
            )}
          </button>

          {/* Messages */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="relative w-9 h-9 rounded-lg bg-white/12 hover:bg-white/20 border border-white/15 flex items-center justify-center transition">
                <Mail className="w-[15px] h-[15px] text-white" />
                {unreadMsgs > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-[#d4b78c] text-[#0a1f4e] text-[10px] font-semibold flex items-center justify-center border border-[#0a1f4e]">
                    {unreadMsgs}
                  </span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80 mr-2">
              <DropdownMenuLabel className="flex items-center justify-between">
                <span>Messages</span>
                <span className="text-xs text-muted-foreground font-normal">{unreadMsgs} non lus</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <div className="max-h-[340px] overflow-y-auto">
                {headerMessages.map((m) => (
                  <DropdownMenuItem key={m.id} className="flex items-start gap-3 py-3 cursor-pointer">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#1e3a8a] to-[#2952a3] text-white text-xs font-semibold flex items-center justify-center flex-shrink-0">
                      {m.initials}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium truncate">{m.name}</p>
                        <span className="text-[10px] text-muted-foreground flex-shrink-0">{m.time}</span>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">{m.message}</p>
                    </div>
                    {m.unread && <span className="w-2 h-2 rounded-full bg-[#d4b78c] mt-2" />}
                  </DropdownMenuItem>
                ))}
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="justify-center text-sm text-[#2952a3] dark:text-[#d4b78c] cursor-pointer">
                Voir tous les messages
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Quick Jump 9-dots — Zayado modules */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                data-testid="header-quickjump-btn"
                className="w-9 h-9 rounded-lg bg-white/12 hover:bg-white/20 border border-white/15 flex items-center justify-center transition"
                aria-label="Modules Zayado"
                title="Modules Zayado"
              >
                <Grid3x3 className="w-[15px] h-[15px] text-white" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72 mr-2 p-3">
              <DropdownMenuLabel className="flex items-center justify-between pb-2">
                <span className="text-xs font-semibold tracking-wider uppercase text-muted-foreground">
                  Écosystème Zayado
                </span>
              </DropdownMenuLabel>
              <div className="grid grid-cols-3 gap-2 pt-1">
                {quickJumpModules.map((m) => {
                  const Icon = quickIconMap[m.icon] || Home;
                  return (
                    <a
                      key={m.id}
                      href={m.url}
                      target={m.external ? '_blank' : undefined}
                      rel={m.external ? 'noopener noreferrer' : undefined}
                      data-testid={`quickjump-${m.id}`}
                      className="zy-tile zy-lift flex flex-col items-center justify-center gap-1.5 p-3 rounded-xl text-center hover:border-[#d4b78c]/50 transition"
                    >
                      <Icon className="w-5 h-5 text-[#2952a3] dark:text-[#d4b78c]" />
                      <span className="text-[11px] font-medium leading-tight">
                        {m.label}
                      </span>
                    </a>
                  );
                })}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="relative w-9 h-9 rounded-lg bg-white/12 hover:bg-white/20 border border-white/15 flex items-center justify-center transition">
                <Bell className="w-[15px] h-[15px] text-white" />
                {unreadNotifs > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-[#d4b78c] text-[#0a1f4e] text-[10px] font-semibold flex items-center justify-center border border-[#0a1f4e]">
                    {unreadNotifs}
                  </span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80 mr-2">
              <DropdownMenuLabel className="flex items-center justify-between">
                <span>Notifications</span>
                <button
                  onClick={() => toast.success('Toutes les notifications marquées comme lues')}
                  className="text-xs text-[#2952a3] dark:text-[#d4b78c] font-normal hover:underline"
                >
                  Tout marquer lu
                </button>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <div className="max-h-[340px] overflow-y-auto">
                {headerNotifications.map((n) => {
                  const Icon = notifIconMap[n.icon] || Bell;
                  return (
                    <DropdownMenuItem key={n.id} className="flex items-start gap-3 py-3 cursor-pointer">
                      <div className="w-9 h-9 rounded-lg zy-tile flex items-center justify-center flex-shrink-0">
                        <Icon className="w-4 h-4 text-[#2952a3] dark:text-[#d4b78c]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{n.title}</p>
                        <p className="text-xs text-muted-foreground">{n.desc}</p>
                        <span className="text-[10px] text-muted-foreground">{n.time}</span>
                      </div>
                      {n.unread && <span className="w-2 h-2 rounded-full bg-[#d4b78c] mt-2" />}
                    </DropdownMenuItem>
                  );
                })}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Profile */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 pl-1 pr-2 h-9 rounded-lg bg-white/12 hover:bg-white/20 border border-white/15 transition">
                <div className="w-7 h-7 rounded-md bg-gradient-to-br from-[#d4b78c] to-[#c4a374] text-[#0a1f4e] text-[11px] font-bold flex items-center justify-center">
                  {userProfile.initials}
                </div>
                <span className="hidden md:inline text-white text-sm font-medium">{userProfile.fullName.split(' ')[0]}</span>
                <ChevronDown className="w-3 h-3 text-white/70 hidden md:block" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60 mr-2">
              <DropdownMenuLabel>
                <div className="flex items-center gap-3 py-1">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#1e3a8a] to-[#2952a3] text-white text-sm font-bold flex items-center justify-center">
                    {userProfile.initials}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold truncate">{userProfile.fullName}</p>
                    <p className="text-xs text-muted-foreground truncate">{userProfile.email}</p>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer">
                <User className="w-4 h-4 mr-2" /> Mon profil
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer">
                <SettingsIcon className="w-4 h-4 mr-2" /> Paramètres
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer">
                <HelpCircle className="w-4 h-4 mr-2" /> Aide & support
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="cursor-pointer text-destructive focus:text-destructive"
                onClick={() => toast.info('Déconnexion mockée')}
              >
                <LogOut className="w-4 h-4 mr-2" /> Déconnexion
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
};

export default Header;
