import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronDown, X, Menu, Globe, Bot, Cpu, MessageSquare, Stethoscope, HardDrive, Image, Zap, Shield, BarChart3, ArrowRight, Users, Sparkles, Code, Clock, Headphones, Target, Crown } from 'lucide-react';
import { useDynamicLogo, useI18n } from "./_stubs";

/* ============================================
   MEGA-MENU DATA — 3 pillars: Assistant IA, Agent IA, Chatbot B2B
   ============================================ */
const ASSISTANT_IA_ITEMS = {
  features: [
    { label: 'ChatGPT, Claude, Gemini, Grok', sub: '8 modeles IA dans une seule interface', href: '/fr/fonctionnalites/assistant-ia', Icon: Bot },
    { label: 'Perplexity — Recherche web', sub: 'Reponses sourcees en temps reel', href: '/fr/fonctionnalites/assistant-ia', Icon: Globe },
    { label: 'Diagnostic holistique', sub: '15 questions, feuille de route strategique', href: '/fr/fonctionnalites/diagnostic-holistique', Icon: Stethoscope },
    { label: 'Drive professionnel', sub: 'OneDrive & Google Drive integres', href: '/fr/fonctionnalites/assistant-ia', Icon: HardDrive },
    { label: "Generation d'images", sub: 'Visuels pro en un clic', href: '/fr/fonctionnalites/assistant-ia', Icon: Image },
    { label: 'Pilotage financier', sub: 'Rentabilite, charges, tresorerie', href: '/fr/fonctionnalites/assistant-ia', Icon: BarChart3 },
  ],
  cta: { label: 'Essai gratuit — 200 credits offerts', href: '/register', highlight: true },
  secondaryCta: { label: 'Voir les tarifs', href: '/fr/tarifs' },
  tagline: 'L\'assistant IA le plus complet pour independants & TPE',
};

const AGENT_IA_ITEMS = {
  features: [
    { label: 'Navigation web autonome', sub: 'L\'agent navigue, extrait et compile pour vous', href: '/fr/fonctionnalites/workflows-automatisation', Icon: Globe },
    { label: 'Rapports automatiques', sub: 'Analyses de marche, veille concurrentielle', href: '/fr/fonctionnalites/workflows-automatisation', Icon: BarChart3 },
    { label: 'Workflows & automatisation', sub: 'Emails, relances, taches recurrentes', href: '/fr/fonctionnalites/workflows-automatisation', Icon: Zap },
    { label: 'Extraction de donnees', sub: 'Sites web, PDF, bases de donnees', href: '/fr/fonctionnalites/workflows-automatisation', Icon: Code },
    { label: 'Agents personnalises', sub: 'Creez vos propres agents metier', href: '/fr/fonctionnalites/workflows-automatisation', Icon: Sparkles },
    { label: 'Planification & declencheurs', sub: 'Horaire, webhook, evenement', href: '/fr/fonctionnalites/workflows-automatisation', Icon: Clock },
  ],
  cta: { label: 'Decouvrir les agents IA', href: '/register', highlight: true },
  secondaryCta: { label: 'Voir une demo', href: '/fr/fonctionnalites/workflows-automatisation' },
  tagline: 'Automatisez les taches complexes avec des agents IA autonomes',
};

const CHATBOT_B2B_ITEMS = {
  features: [
    { label: 'Chatbot pour votre site', sub: 'Widget integrable en 1 clic', href: '/fr/chatbot-b2b', Icon: MessageSquare },
    { label: 'Support client 24/7', sub: 'Reponses instantanees, base de connaissances', href: '/fr/chatbot-b2b', Icon: Headphones },
    { label: 'WordPress & WooCommerce', sub: 'Plugin natif, installation sans code', href: '/fr/chatbot-b2b', Icon: Code },
    { label: 'Analytics & Export leads', sub: 'Suivez les conversations, exportez en Excel', href: '/fr/chatbot-b2b', Icon: BarChart3 },
    { label: 'Personnalisation marque', sub: 'Couleurs, ton, avatar — a votre image', href: '/fr/chatbot-b2b', Icon: Target },
    { label: 'Multi-canal (bientot)', sub: 'WhatsApp, Telegram, Microsoft Teams', href: '/fr/chatbot-b2b', Icon: Users },
  ],
  cta: { label: 'Creer mon chatbot gratuitement', href: '/register', highlight: true },
  secondaryCta: { label: 'Voir les exemples', href: '/fr/chatbot-b2b' },
  tagline: 'Transformez chaque visiteur en client avec un chatbot IA',
};

/* ============================================
   SHARED COMPONENTS
   ============================================ */
function MegaLink({ label, sub, href, Icon, onClose }) {
  return (
    <Link
      to={href}
      onClick={onClose}
      className="flex items-start gap-3 px-3 py-2.5 rounded-lg text-gray-700 hover:bg-[#f5f0e8] hover:text-[#0F1E3C] transition-all group"
    >
      <div className="w-8 h-8 rounded-lg bg-[#1D4E8A]/8 flex items-center justify-center shrink-0 group-hover:bg-[#1D4E8A]/15 transition-colors">
        <Icon className="w-4 h-4 text-[#1D4E8A]" />
      </div>
      <div>
        <span className="text-[13px] font-semibold block text-gray-800 group-hover:text-[#1D4E8A]">{label}</span>
        {sub && <span className="block text-[11px] text-gray-400 mt-0.5 leading-relaxed">{sub}</span>}
      </div>
    </Link>
  );
}

function MegaPanel({ data, onClose, accentColor = '#1D4E8A' }) {
  return (
    <div
      className="absolute top-full left-1/2 -translate-x-1/2 mt-1 bg-white rounded-xl shadow-2xl border border-gray-100 z-[100] animate-fadeDown overflow-hidden"
      style={{ width: 560 }}
      data-testid="mega-panel"
    >
      {/* Tagline bar */}
      <div className="px-5 py-2.5 bg-gradient-to-r from-[#0F1E3C] to-[#1D4E8A]">
        <p className="text-[11px] font-semibold text-white/90 tracking-wide">{data.tagline}</p>
      </div>

      {/* Features grid */}
      <div className="p-4 grid grid-cols-2 gap-0.5">
        {data.features.map((item, i) => (
          <MegaLink key={i} {...item} onClose={onClose} />
        ))}
      </div>

      {/* CTA bar */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#F5F3EF] border-t border-[#E2DDD5]">
        <Link
          to={data.cta.href}
          onClick={onClose}
          className="flex items-center gap-2 px-4 py-2 text-[12px] font-bold text-white bg-[#C7372F] hover:bg-[#a82d26] rounded-lg transition-colors shadow-sm"
          data-testid="mega-cta-primary"
        >
          {data.cta.label} <ArrowRight className="w-3.5 h-3.5" />
        </Link>
        <Link
          to={data.secondaryCta.href}
          onClick={onClose}
          className="text-[12px] font-semibold text-[#1D4E8A] hover:underline"
          data-testid="mega-cta-secondary"
        >
          {data.secondaryCta.label} →
        </Link>
      </div>
    </div>
  );
}

function LanguageToggle() {
  const { lang, setLang } = useI18n();
  const nextLang = lang === 'fr' ? 'en' : 'fr';
  return (
    <button
      onClick={() => setLang(nextLang)}
      className="flex items-center gap-1.5 px-2.5 py-1.5 text-[12px] font-medium text-gray-500 hover:text-[#1D4E8A] hover:bg-gray-50 rounded-md transition-all"
      data-testid="lang-toggle"
      title={lang === 'fr' ? 'Switch to English' : 'Passer en francais'}
    >
      <Globe className="w-3.5 h-3.5" />
      {lang === 'fr' ? 'EN' : 'FR'}
    </button>
  );
}

/* ============================================
   NAV ITEM WITH MEGA MENU (reusable)
   ============================================ */
function NavItemWithMega({ label, icon: IconComp, data, testId }) {
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);

  const handleEnter = () => { clearTimeout(timerRef.current); setOpen(true); };
  const handleLeave = () => { timerRef.current = setTimeout(() => setOpen(false), 180); };

  return (
    <li className="relative" onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
      <button
        className={`flex items-center gap-1.5 px-3 py-2 text-[13px] font-semibold rounded-md transition-all ${
          open ? 'text-[#1D4E8A] bg-[#1D4E8A]/5' : 'text-gray-600 hover:text-[#1D4E8A] hover:bg-gray-50'
        }`}
        data-testid={testId}
      >
        <IconComp className="w-3.5 h-3.5" />
        {label}
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <MegaPanel data={data} onClose={() => setOpen(false)} />}
    </li>
  );
}

/* ============================================
   MAIN NAV COMPONENT
   ============================================ */
export default function MegaMenuNav() {
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { logoUrl } = useDynamicLogo();

  return (
    <>
      <style>{`
        @keyframes fadeDown {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeDown { animation: fadeDown 0.2s ease; }
      `}</style>

      <nav className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm" data-testid="mega-menu-nav">
        <div className="max-w-[1280px] mx-auto px-6 flex items-center justify-between" style={{ height: 64 }}>

          {/* Logo */}
          <a href="https://zayado.net" className="flex items-center gap-2 shrink-0" data-testid="mega-logo">
            {logoUrl ? (
              <img src={logoUrl} alt="ZAYADO" className="h-8 w-auto object-contain" />
            ) : (
              <span className="text-[#1D4E8A] font-extrabold text-xl tracking-widest">ZAYADO<span className="text-[#E5D5A2]">.</span></span>
            )}
          </a>

          {/* Desktop Menu — 3 mega menus + Tarifs + Contact */}
          <ul className="hidden lg:flex items-center gap-0.5 list-none flex-1 justify-center">
            <NavItemWithMega label="Assistant IA" icon={Bot} data={ASSISTANT_IA_ITEMS} testId="nav-assistant-ia" />
            <NavItemWithMega label="Agent IA" icon={Cpu} data={AGENT_IA_ITEMS} testId="nav-agent-ia" />
            <NavItemWithMega label="Chatbot B2B" icon={MessageSquare} data={CHATBOT_B2B_ITEMS} testId="nav-chatbot-b2b" />

            <li>
              <Link to="/fr/tarifs" className="px-3 py-2 text-gray-600 text-[13px] font-semibold rounded-md hover:text-[#1D4E8A] hover:bg-gray-50 transition-all" data-testid="nav-tarifs">
                Tarifs
              </Link>
            </li>
            <li>
              <a href="https://zayado.net/contact" className="px-3 py-2 text-gray-600 text-[13px] font-semibold rounded-md hover:text-[#1D4E8A] hover:bg-gray-50 transition-all" data-testid="nav-contact">
                Contact
              </a>
            </li>
          </ul>

          {/* Right side: Language + Connexion + CTA */}
          <div className="hidden lg:flex items-center gap-2 shrink-0">
            <LanguageToggle />
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-[13px] font-semibold rounded-lg border border-[#1D4E8A] text-[#1D4E8A] hover:bg-[#1D4E8A] hover:text-white transition-all"
              data-testid="mega-login-btn"
            >
              Connexion
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-4 py-2 text-[13px] font-bold rounded-lg bg-[#C7372F] text-white hover:bg-[#a82d26] transition-all shadow-sm"
              data-testid="mega-register-btn"
            >
              Essai gratuit
            </button>
          </div>

          {/* Mobile hamburger */}
          <button className="lg:hidden text-gray-700 p-2" onClick={() => setMobileOpen(!mobileOpen)} data-testid="hamburger-btn">
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="lg:hidden fixed inset-0 z-[200]" data-testid="mobile-sidebar">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
            <aside className="absolute top-0 right-0 h-full w-[300px] bg-white shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <a href="https://zayado.net">
                  {logoUrl ? (
                    <img src={logoUrl} alt="ZAYADO" className="h-8 object-contain" />
                  ) : (
                    <span className="text-[#1D4E8A] font-extrabold text-lg tracking-widest">ZAYADO<span className="text-[#E5D5A2]">.</span></span>
                  )}
                </a>
                <button onClick={() => setMobileOpen(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
                <MobileAccordion label="Assistant IA" icon={Bot} items={ASSISTANT_IA_ITEMS.features} onClose={() => setMobileOpen(false)} testId="mobile-assistant-ia" />
                <MobileAccordion label="Agent IA" icon={Cpu} items={AGENT_IA_ITEMS.features} onClose={() => setMobileOpen(false)} testId="mobile-agent-ia" />
                <MobileAccordion label="Chatbot B2B" icon={MessageSquare} items={CHATBOT_B2B_ITEMS.features} onClose={() => setMobileOpen(false)} testId="mobile-chatbot-b2b" />
                <Link to="/fr/tarifs" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 font-semibold rounded-xl hover:bg-gray-50" data-testid="mobile-tarifs">
                  <Crown className="w-4 h-4 text-[#C9A84C]" /> Tarifs
                </Link>
                <a href="https://zayado.net/contact" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 font-semibold rounded-xl hover:bg-gray-50" data-testid="mobile-contact">
                  Contact
                </a>
              </div>
              <div className="px-4 pb-6 pt-3 border-t border-gray-100 space-y-2">
                <LanguageToggle />
                <button onClick={() => { setMobileOpen(false); navigate('/register'); }} className="block w-full text-center px-3 py-3 text-white text-sm font-bold rounded-xl bg-[#C7372F] hover:bg-[#a82d26] transition-all" data-testid="mobile-register">
                  Essai gratuit — 200 credits
                </button>
                <button onClick={() => { setMobileOpen(false); navigate('/login'); }} className="block w-full text-center px-3 py-3 text-[#1D4E8A] text-sm font-bold rounded-xl border border-[#1D4E8A] hover:bg-[#1D4E8A] hover:text-white transition-all" data-testid="mobile-connexion">
                  Connexion
                </button>
              </div>
            </aside>
          </div>
        )}
      </nav>
    </>
  );
}

/* ============================================
   MOBILE ACCORDION (reusable)
   ============================================ */
function MobileAccordion({ label, icon: IconComp, items, onClose, testId }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center justify-between w-full px-3 py-2.5 text-sm font-semibold rounded-xl transition-colors ${open ? 'text-[#1D4E8A] bg-[#1D4E8A]/5' : 'text-gray-700 hover:bg-gray-50'}`}
        data-testid={testId}
      >
        <span className="flex items-center gap-2">
          <IconComp className="w-4 h-4 text-[#1D4E8A]" />
          {label}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="ml-2 space-y-0.5 pb-1 animate-fadeDown">
          {items.map((item, i) => (
            <Link key={i} to={item.href} onClick={onClose} className="flex items-start gap-2.5 px-3 py-2 rounded-lg hover:bg-gray-50">
              <item.Icon className="w-4 h-4 mt-0.5 text-[#1D4E8A]" />
              <div>
                <span className="text-sm font-medium text-gray-700">{item.label}</span>
                <span className="block text-[11px] text-gray-400">{item.sub}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
