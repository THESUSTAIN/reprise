import React, { useState, useRef, useEffect, useContext } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { useStreaming } from '../context/StreamingContext';
import { Send, Plus, Zap, Brain, Bot, MessageSquare, Sparkles, Copy, ThumbsUp, ThumbsDown, RefreshCw, FileDown, Headphones, Paperclip, Mic, MicOff, Loader2, Globe, Flame, Search, Image, Camera, ChevronDown, AlertTriangle, Key, Settings, X, ExternalLink, Info, Upload, Cloud, CloudOff, RefreshCcw, Square, Check, CreditCard } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { mainModes, extraModes, imageModels, getCategories, getProPromptLibrary, getQuickPromptCategories } from './chat/chatConfig';
import MarkdownContent from './chat/MarkdownContent';
import { AgentAnimation } from './chat/AgentAnimation';
import { useTaskNotification } from '../hooks/useTaskNotification';
import TaskCompleteAnimation from './TaskCompleteAnimation';
import { SlashCommandMenu, SLASH_COMMANDS } from './chat/SlashCommandMenu';
import ConversationSummaryCard from './chat/ConversationSummaryCard';

const API = process.env.REACT_APP_BACKEND_URL || '';

/* Constants (mainModes, extraModes, imageModels, getCategories) imported from chat/chatConfig.js */
/* MarkdownContent imported from chat/MarkdownContent.js */

export const ChatInterface = ({ initialConversationId, onFilesChange, onConversationChange }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, updateUser, refreshUser } = useContext(AuthContext);
  const { t, lang } = useI18n();
  const streaming = useStreaming();
  const modes = mainModes(lang);
  const extras = extraModes(lang);
  const categories = getCategories(lang);
  const quickPromptCats = getQuickPromptCategories(lang);
  const [quickCat, setQuickCat] = useState('populaires');
  const [mode, setMode] = useState(() => {
    // Use user's default mode preference if no conversation is loaded
    if (!initialConversationId && user?.settings?.default_mode) {
      const validModes = ['byok', 'fast', 'pro', 'gemini', 'grok', 'perplexity'];
      if (validModes.includes(user.settings.default_mode)) return user.settings.default_mode;
    }
    if (!initialConversationId && user?.settings?.defaultMode) {
      const validModes = ['byok', 'fast', 'pro', 'gemini', 'grok', 'perplexity'];
      if (validModes.includes(user.settings.defaultMode)) return user.settings.defaultMode;
    }
    return 'fast';
  });
  const [showExtraModes, setShowExtraModes] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);
  // Image states via StreamingContext (persistent à la navigation)
  const {
    isImageGenerating,
    imageProgress,
    startImageGeneration,
    completeImageGeneration,
    cancelImageGeneration,
  } = streaming || {};
  const [conversationId, setConversationId] = useState(initialConversationId || null);
  const [manusPolling, setManusPolling] = useState(false);
  const [agentSteps, setAgentSteps] = useState([]); // animated agent steps
  const [thinkingPhrase, setThinkingPhrase] = useState(0); // rotating thinking phrase
  const [modeTransferDialog, setModeTransferDialog] = useState(null); // { pendingMode, pendingImageMode }
  const [supportHumain, setSupportHumain] = useState({ has: false, active: false });

  // Show support button for paid users or when credits are low
  useEffect(() => {
    const totalCredits = (user?.credits || 0) + (user?.bonus_credits || 0) + (user?.purchased_credits || 0);
    const isPaidUser = user?.plan && user.plan !== 'free';
    const lowCredits = totalCredits < 10;
    setSupportHumain(prev => ({ ...prev, has: isPaidUser || lowCredits }));
  }, [user]);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);
  const [selectedTextCat, setSelectedTextCat] = useState(null);
  const [showByokModal, setShowByokModal] = useState(false);
  const [showAgentConfirm, setShowAgentConfirm] = useState(false);
  const [pendingAgentMessage, setPendingAgentMessage] = useState(null);
  const [imageMode, setImageMode] = useState(false);
  const [imageModel, setImageModel] = useState('nano-banana');
  const [showImageMenu, setShowImageMenu] = useState(false);
  const [agentActive, setAgentActive] = useState(false);
  const agentWsRef = useRef(null); // WebSocket ref for agent cancellation
  const [showSyncMenu, setShowSyncMenu] = useState(false);
  const [showPlusMenu, setShowPlusMenu] = useState(false);
  const plusMenuRef = useRef(null);
  const [showChatInfo, setShowChatInfo] = useState(false);
  const [chatZoom, setChatZoom] = useState(() => { try { return parseInt(localStorage.getItem('zayado_chat_zoom') || '90'); } catch { return 90; } });
  const [feedbacks, setFeedbacks] = useState({});
  const [showPromptsDropdown, setShowPromptsDropdown] = useState(false);
  const [promptsList, setPromptsList] = useState([]);
  const [systemPrompts, setSystemPrompts] = useState([]);
  const [userPrompts, setUserPrompts] = useState([]);
  const [showAddPrompt, setShowAddPrompt] = useState(false);
  const [newPromptTitle, setNewPromptTitle] = useState('');
  const [newPromptText, setNewPromptText] = useState('');
  const [newPromptAction, setNewPromptAction] = useState('insert');
  const [savingPrompt, setSavingPrompt] = useState(false);

  // Custom Agents selector
  const [customAgents, setCustomAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null); // null = default Extension IA
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const agentToggleRef = useRef(null);
  const [agentPickerPos, setAgentPickerPos] = useState({ top: 0, left: 0 });

  // Slash commands menu
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashActiveIdx, setSlashActiveIdx] = useState(0);

  // Welcome screen widgets
  const [serenityScore, setSerenityScore] = useState(null);
  const [activeTimer, setActiveTimer] = useState(null);

  const selectAgent = async (agent) => {
    setSelectedAgent(agent);
    setShowAgentPicker(false);
    if (!agent) return; // back to default
    // Load agent conversation history
    try {
      const r = await fetch(`${API}/api/custom-agents/${agent.id}/history`, { headers: { Authorization: `Bearer ${token}` } });
      if (r.status === 404) {
        toast.error('Cet agent a été supprimé. Retour en mode standard.');
        return;
      }
      if (r.ok) {
        const history = await r.json();
        if (history.length > 0) {
          const agentMsgs = history.map(m => ({ role: m.role, content: m.content, agentName: m.role === 'assistant' ? agent.name : undefined }));
          setMessages(prev => [...prev, { role: 'system', content: `--- ${agent.name} ---`, isAgentSwitch: true }, ...agentMsgs]);
        }
      }
    } catch (e) { /* silencieux */ }
  };

  // Task completion animation state
  const [showTaskComplete, setShowTaskComplete] = useState(false);
  const [taskCompleteData, setTaskCompleteData] = useState({ taskType: 'agent', message: '', creditsUsed: 0 });
  
  // Notification hook
  const { notifyTaskComplete } = useTaskNotification({ 
    soundType: 'success', 
    volume: 0.6,
    enableBrowserNotification: true,
    enableSound: true 
  });

  // Complexity detection state
  const [complexitySuggestion, setComplexitySuggestion] = useState(null);
  const [showComplexityHint, setShowComplexityHint] = useState(false);
  const complexityDebounceRef = useRef(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const pendingAutoSendRef = useRef(null); // For quick prompt auto-send
  // Drive nudge banner — shown max 2 times, stored in localStorage
  const [showDriveNudge, setShowDriveNudge] = useState(false);
  
  // Get token early to avoid temporal dead zone
  const token = localStorage.getItem('zayado_token');

  // Sync drive status
  const [driveConnected, setDriveConnected] = useState({ google: false, onedrive: false });
  const [syncingDrive, setSyncingDrive] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState(() => safeLocalGet('zayado_last_sync_time')`;
    const cached = sessionStorage.getItem(cacheKey);
    const cacheTime = parseInt(sessionStorage.getItem(cacheKey + '_t') || '0');
    const now = Date.now();
    if (cached && now - cacheTime < 60000) {
      try {
        const d = JSON.parse(cached);
        _applyInitData(d);
        return;
      } catch (e) { /* silencieux */ }
    }
    fetch(`${API}/api/chat/init`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        sessionStorage.setItem(cacheKey, JSON.stringify(d));
        sessionStorage.setItem(cacheKey + '_t', String(Date.now()));
        _applyInitData(d);
      })
      .catch(() => {});
  // eslint-disable-next-line
  }, [token]);

  const _applyInitData = (d) => {
    // Drive status
    if (d.drive_connected) {
      setDriveConnected({ google: d.drive_connected.google, onedrive: d.drive_connected.onedrive });
      const count = parseInt(safeLocalGet('zayado_drive_nudge')
    // Custom agents
    if (d.custom_agents) setCustomAgents(d.custom_agents);
    // Support humain
    if (d.support_humain) setSupportHumain({ has: d.support_humain.has, active: d.support_humain.active });
    // Timer actif
    if (d.active_timer) setActiveTimer(d.active_timer);
  };

  // Pré-remplir le champ de saisie depuis location.state.prefillMessage (navigation depuis d'autres pages)
  useEffect(() => {
    const prefill = location?.state?.prefillMessage;
    if (prefill && typeof prefill === 'string' && prefill.trim()) {
      setMessage(prefill.trim());
      // Effacer le state pour éviter le re-remplissage lors des navigations suivantes
      window.history.replaceState({}, document.title);
      // Focus sur le champ de saisie
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [location?.state?.prefillMessage]);

  // FIX: custom agents chargés via /init (supprimé pour performance)

  // FIX: serenity + timer chargés via /init (supprimé pour performance)

  const mediaRecorderRef = useRef(null);
  const manusPollingRef = useRef(null);

  const [conversationCreatedAt, setConversationCreatedAt] = useState(null);
  const [totalCreditsUsed, setTotalCreditsUsed] = useState(0);
  const chatInfoRef = useRef(null);

  // Close popover/dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (showChatInfo && chatInfoRef.current && !chatInfoRef.current.contains(e.target) && !e.target.closest('[data-testid="chat-info-btn-modebar"]')) {
        setShowChatInfo(false);
      }
      if (showExtraModes &&
        !e.target.closest('[data-testid="extra-modes-btn"]') &&
        !e.target.closest('[data-testid="extra-modes-dropdown"]') &&
        !e.target.closest('[data-testid="mobile-mode-dropdown"]') &&
        !e.target.closest('[data-testid="mobile-mode-dropdown-empty"]') &&
        !e.target.closest('[data-testid="mobile-mode-menu"]') &&
        !e.target.closest('[data-testid="mobile-mode-menu-empty"]')
      ) {
        setShowExtraModes(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showChatInfo, showExtraModes]);

  // Compute credits used for this conversation (sum per-message credit_cost)
  const creditsUsed = messages.reduce((acc, m) => {
    if (m.role === 'user') {
      if (typeof m.credit_cost === 'number') return acc + m.credit_cost;
      // Fallback for older messages without credit_cost
      const msgMode = m.mode || mode;
      const cost = { fast: 1, pro: 3, gemini: 2, grok: 2, perplexity: 3, image: 5, agent: 50 }[msgMode] || 0;
      return acc + cost;
    }
    return acc;
  }, 0);

  // ---- Mode switching avec transfert d'historique optionnel ----
  const handleModeChange = (newModeId, newImageMode = false) => {
    // Bug 12 : vérifier que le mode est autorisé selon le plan
    const plan = user?.plan || 'free';
    const MODE_PLAN_REQUIREMENTS = {
      pro: ['pro', 'business', 'team', 'admin'],
      advanced: ['pro', 'business', 'team', 'admin'],
      gemini: ['productivite', 'pro', 'business', 'team', 'admin'],
      grok: ['pro', 'business', 'team', 'admin'],
      perplexity: ['pro', 'business', 'team', 'admin'],
      image: ['productivite', 'pro', 'business', 'team', 'admin'],
    };
    const required = MODE_PLAN_REQUIREMENTS[newModeId];
    if (required && !required.includes(plan)) {
      toast.error('Mode non disponible avec votre plan — passez au plan supérieur');
      return;
    }
    const hasConversation = messages.length > 0 && conversationId;
    if (hasConversation) {
      setModeTransferDialog({ pendingMode: newModeId, pendingImageMode: newImageMode });
    } else {
      applyModeChange(newModeId, newImageMode, false);
    }
  };

  const applyModeChange = (newModeId, newImageMode, keepHistory) => {
    // Always just change the mode — never navigate away or reset conversation
    // User explicitly chose "keep history" or "new conversation" 
    if (!keepHistory) {
      setMessages([]);
      setConversationId(null);
      setManusPolling(false);
    }
    setMode(newModeId);
    setImageMode(newImageMode);
    setShowExtraModes(false);
    setModeTransferDialog(null);
    // Do NOT navigate — stay on current page, just switch mode
  };

  // Notify parent of conversation ID changes + update URL
  useEffect(() => {
    if (onConversationChange) onConversationChange(conversationId);
    // Navigate to conversation URL when a new conversation is created
    if (conversationId && !initialConversationId && window.location.pathname !== `/app/chat/${conversationId}`) {
      navigate(`/app/chat/${conversationId}`, { replace: true });
    }
  }, [conversationId]); // eslint-disable-line

  const userScrolledUp = useRef(false);
  const streamScrollTimer = useRef(null);

  const scrollToBottom = (force = false) => {
    if (!userScrolledUp.current || force) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Auto-scroll on new messages
  useEffect(scrollToBottom, [messages]);

  // Smooth auto-scroll during streaming (every 300ms)
  useEffect(() => {
    if (isStreaming) {
      streamScrollTimer.current = setInterval(() => {
        if (!userScrolledUp.current) {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
      }, 300);
    }
    return () => { if (streamScrollTimer.current) clearInterval(streamScrollTimer.current); };
  }, [isStreaming]);

  // Auto-scroll when agent steps update
  useEffect(() => {
    if (agentSteps.length > 0 && !userScrolledUp.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agentSteps]);

  const handleScroll = (e) => {
    const el = e.target;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distFromBottom > 200);
    userScrolledUp.current = distFromBottom > 150;
  };

  // Cancel agent WebSocket
  const cancelAgent = () => {
    if (agentWsRef.current) {
      try { agentWsRef.current.close(); } catch {}
      agentWsRef.current = null;
    }
    setIsStreaming(false); if (window._streamTimeout) { clearTimeout(window._streamTimeout); window._streamTimeout = null; }
    setManusPolling(false);
    setAgentSteps(prev => [
      ...prev.map(s => ({ ...s, status: s.status === 'active' ? 'error' : s.status })),
      { type: 'error', message: 'Tache annulee par l\'utilisateur', status: 'error', timestamp: Date.now() }
    ]);
    setMessages(prev => {
      const updated = [...prev];
      if (updated.length > 0 && updated[updated.length - 1].role === 'assistant') {
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: updated[updated.length - 1].content + '\n\n_Tache annulee._'
        };
      }
      return updated;
    });
  };

  // Complexity detection: analyze message as user types (debounced)
  useEffect(() => {
    if (!message.trim() || message.length < 15) {
      setComplexitySuggestion(null);
      setShowComplexityHint(false);
      return;
    }
    
    // Debounce: wait 800ms after user stops typing
    if (complexityDebounceRef.current) clearTimeout(complexityDebounceRef.current);
    complexityDebounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/complexity/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            message: message,
            file_count: attachedFiles.length,
            file_pages: 0, // Would need PDF page count
            exchange_count: messages.length,
            current_model: imageMode ? 'image' : mode
          })
        });
        if (res.ok) {
          const data = await res.json();
          setComplexitySuggestion(data);
          // Show hint only if upgrade is recommended
          // Ne pas réafficher si l'utilisateur a ignoré pour cette session
          const dismissed = sessionStorage.getItem('zayado_complexity_dismissed') === '1';
          setShowComplexityHint(!dismissed && data.upgrade_hint && !data.current_model_ok);
        }
      } catch (err) {
        // // console.log('Complexity check failed:', err);
      }
    }, 800);
    
    return () => {
      if (complexityDebounceRef.current) clearTimeout(complexityDebounceRef.current);
    };
  }, [message, mode, imageMode, attachedFiles.length, messages.length, token]);

  // Rotate thinking phrase every 3s while streaming
  useEffect(() => {
    if (!isStreaming) { setThinkingPhrase(0); return; }
    const iv = setInterval(() => setThinkingPhrase(p => (p + 1) % 5), 3000);
    return () => clearInterval(iv);
  }, [isStreaming]);

  // Animate agent steps progressively when manusPolling starts
  useEffect(() => {
    if (!manusPolling) { setAgentSteps([]); return; }
    const stepDefs = [
      { icon: '', label: 'Analyse de votre demande' },
      { icon: '', label: 'Identification des détails clés' },
      { icon: '', label: 'Recherche d informations pertinentes' },
      { icon: '', label: 'Collecte des données recueillies' },
      { icon: '', label: 'Génération de la réponse...' },
    ];
    let idx = 0;
    setAgentSteps([]);
    const iv = setInterval(() => {
      if (idx < stepDefs.length) {
        setAgentSteps(prev => [...prev, stepDefs[idx]]);
        idx++;
      } else {
        clearInterval(iv);
      }
    }, 1800);
    return () => clearInterval(iv);
  }, [manusPolling]);

  // Listen for custom prompt insertion from right panel
  useEffect(() => {
    const handler = (e) => {
      const { prompt, action } = e.detail || {};
      if (!prompt) return;
      if (action === 'auto_send') {
        // Auto-set sync choice to prevent sync prompt blocking
        if (!localStorage.getItem('zayado_sync_choice') {
          localStorage.setItem('zayado_sync_choice', 'internal');
        }
        // Use pending ref for reliable auto-send (avoids stale closure)
        pendingAutoSendRef.current = prompt;
        setMessage(prompt);
      } else {
        setMessage(prompt);
        inputRef.current?.focus();
      }
    };
    window.addEventListener('insertPrompt', handler);
    return () => window.removeEventListener('insertPrompt', handler);
  }, []);

  // Load existing conversation
  useEffect(() => {
    if (initialConversationId && token) {
      fetch(`${API}/api/chat/conversations/${initialConversationId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => {
          if (r.status === 404) {
            toast.error('Conversation introuvable ou supprimee');
            navigate('/app');
            return null;
          }
          if (!r.ok) {
            toast.error('Erreur lors du chargement de la conversation');
            return null;
          }
          return r.json();
        })
        .then(data => {
          if (data?.messages) {
            const cleanedMessages = data.messages.map(msg => {
              if (msg.role === 'user' && msg.fileContext) {
                return { ...msg, fileContext: undefined };
              }
              return msg;
            });
            setMessages(cleanedMessages);
            if (data.mode) setMode(data.mode);
            if (data.created_at) setConversationCreatedAt(data.created_at);
            if (typeof data.total_credits_used === 'number') setTotalCreditsUsed(data.total_credits_used);
          }
        })
        .catch(() => {
          toast.error('Erreur de connexion');
          navigate('/app');
        });
    }
  }, [initialConversationId, token]);

  // Load feedbacks for conversation
  useEffect(() => {
    if (!initialConversationId || !token) { setFeedbacks({}); return; }
    fetch(`${API}/api/chat/feedback/${initialConversationId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : {})
      .then(data => setFeedbacks(data || {}))
      .catch(() => {});
  }, [initialConversationId, token]);

  const submitFeedback = async (msgIndex, type) => {
    if (!conversationId || !token) return;
    try {
      const res = await fetch(`${API}/api/chat/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ conversation_id: conversationId, message_index: msgIndex, feedback: type })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'removed') {
          setFeedbacks(prev => { const n = {...prev}; delete n[String(msgIndex)]; return n; });
        } else {
          setFeedbacks(prev => ({ ...prev, [String(msgIndex)]: type }));
        }
      }
    } catch (e) { /* silencieux */ }
  };

  // FIX: support-status chargé via /init (supprimé pour performance)

  const handleExportPDF = async () => {
    if (!conversationId) return;
    try {
      const res = await fetch(`${API}/api/chat/conversations/${conversationId}/export-pdf`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = `zayado-${conversationId.slice(0, 8)}.pdf`; a.click();
        URL.revokeObjectURL(url);
        toast.success(lang === 'en' ? 'Conversation exported!' : 'Conversation exportée !');
      }
    } catch { toast.error(lang === 'en' ? 'Export error' : "Erreur d'export"); }
  };

  // Save content to the configured cloud drive (Google Drive, OneDrive, or SharePoint)
  const saveToDrive = async (content, contentType = 'text', filename = '') => {
    const syncSource = safeLocalGet('zayado_autosync_source')
    }
    try {
      let res;
      const ts = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', 'h');
      const autoFilename = filename || `conversation_${ts}.md`;
      if (provider === 'gdrive') {
        res = await fetch(`${API}/api/drive/autosave`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ content, content_type: contentType, filename: autoFilename })
        });
      } else if (provider === 'onedrive') {
        const blob = new Blob([content], { type: 'text/plain' });
        const form = new FormData();
        form.append('file', blob, autoFilename);
        res = await fetch(`${API}/api/onedrive/upload?folder_path=Extension%20IA%2FDocuments%20%26%20PDF`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: form
        });
      } else if (provider === 'sharepoint') {
        const siteId = safeLocalGet('zayado_sp_site_id')
        res = await fetch(`${API}/api/onedrive/sharepoint/autosave?site_id=${encodeURIComponent(siteId)}&content_type=${contentType}&filename=${encodeURIComponent(autoFilename)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ content, content_type: contentType, filename: autoFilename, site_id: siteId })
        });
      }
      if (res?.ok) {
        const data = await res.json();
        const now = new Date().toLocaleString('fr-FR');
        localStorage.setItem('zayado_last_sync_time', now);
        setLastSyncTime(now);
        const providerLabel = provider === 'gdrive' ? 'Google Drive' : provider === 'onedrive' ? 'OneDrive' : 'SharePoint';
        toast.success(
          <div className="flex items-center gap-2">
            <Cloud className="w-4 h-4" />
            <span>Sauvegardé sur {providerLabel}</span>
            {data.webViewLink && <a href={data.webViewLink} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline text-xs ml-1">Voir</a>}
          </div>
        );
        return data;
      } else {
        const err = await res?.json().catch(() => ({}));
        if (err.detail?.includes('non connecte') || err.detail?.includes('non configure')) {
          toast.error('Connectez votre Drive dans Paramètres → Drive Pro');
        } else {
          toast.error('Erreur de sauvegarde cloud');
        }
      }
    } catch {
      toast.error('Erreur de connexion cloud');
    }
    return null;
  };

  const [supportModalOpen, setSupportModalOpen] = useState(false);
  const [supportMessage, setSupportMessage] = useState('');

  const toggleSupportHumain = () => {
    setSupportModalOpen(true);
  };

  const submitSupportRequest = async () => {
    try {
      const res = await fetch(`${API}/api/chat/support-humain/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: supportMessage,
          messages_count: messages.length,
          mode: mode,
        })
      });
      if (res.ok) {
        toast.success('Demande de support envoyée ! Un agent vous contactera bientôt.');
        setSupportModalOpen(false);
        setSupportMessage('');
        setSupportHumain(s => ({ ...s, active: true }));
      } else if (res.status === 403) {
        toast.info("Le support humain n'est pas inclus dans votre forfait actuel. Contactez-nous à contact@zayado.net ou passez à un forfait supérieur pour en bénéficier.", { duration: 6000 });
        setSupportModalOpen(false);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erreur');
      }
    } catch { toast.error('Erreur de connexion'); }
  };

  // File upload handler
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    const MAX_SIZE = 25 * 1024 * 1024; // 25 Mo
    const oversized = files.filter(f => f.size > MAX_SIZE);
    if (oversized.length > 0) {
      toast.error(`Fichier trop volumineux (max 25 Mo) : ${oversized.map(f => f.name).join(', ')}`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setUploadingFile(true);
    const newFiles = [];
    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${API}/api/chat/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });
        if (res.ok) {
          const data = await res.json();
          newFiles.push({ name: file.name, type: file.type, url: data.url, id: data.id, extracted_text: data.extracted_text || "", ext: data.ext || "" });
        } else {
          toast.error(`Erreur upload: ${file.name}`);
        }
      } catch {
        toast.error(`Erreur upload: ${file.name}`);
      }
    }
    setAttachedFiles(prev => {
      const next = [...prev, ...newFiles];
      if (onFilesChange) onFilesChange(next);
      return next;
    });
    setUploadingFile(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (idx) => setAttachedFiles(prev => {
    const next = prev.filter((_, i) => i !== idx);
    if (onFilesChange) onFilesChange(next);
    return next;
  });

  // Voice recording
  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', blob, 'voice.webm');
        try {
          const res = await fetch(`${API}/api/chat/transcribe`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData
          });
          if (res.ok) {
            const data = await res.json();
            if (data.text) setMessage(prev => prev + data.text);
          } else {
            toast.error('Erreur de transcription');
          }
        } catch {
          toast.error('Erreur de transcription');
        }
      };
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      toast.success('Enregistrement en cours...');
    } catch {
      toast.error('Microphone non disponible');
    }
  };

  // Poll for Manus task updates — fast polling every 3 seconds
  useEffect(() => {
    if (manusPolling && conversationId && token) {
      let attempts = 0;
      const maxAttempts = 120; // 6 minutes max

      // Immediately check once
      const checkManus = async () => {
        try {
          const res = await fetch(`${API}/api/chat/conversations/${conversationId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            if (data?.messages) {
              setMessages(data.messages);
              // If manus_task_id is null, the backend finished processing
              if (!data.manus_task_id) {
                const lastMsg = data.messages[data.messages.length - 1];
                if (lastMsg?.role === 'assistant' && lastMsg.content && lastMsg.content.length > 50) {
                  return true; // Done
                }
              }
              const lastMsg = data.messages[data.messages.length - 1];
              if (lastMsg?.role === 'assistant' && lastMsg.content &&
                  !lastMsg.content.includes('Traitement de votre demande') &&
                  !lastMsg.content.includes('en cours') &&
                  lastMsg.content.length > 50) {
                return true;
              }
            }
          }
        } catch (e) { /* silencieux */ }
        return false;
      };

      // Initial check
      checkManus().then(done => {
        if (done) {
          setManusPolling(false);
          return;
        }
      });

      manusPollingRef.current = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
          clearInterval(manusPollingRef.current);
          setManusPolling(false);
          return;
        }
        const done = await checkManus();
        if (done) {
          clearInterval(manusPollingRef.current);
          setManusPolling(false);
        }
      }, 3000);

      return () => {
        if (manusPollingRef.current) clearInterval(manusPollingRef.current);
      };
    }
  }, [manusPolling, conversationId, token]);

  // Abort streaming
  const abortStreamingRef = React.useRef(null);
  const handleAbort = async () => {
    if (abortStreamingRef.current) {
      abortStreamingRef.current.abort();
      abortStreamingRef.current = null;
    }
    if (conversationId) {
      try {
        await fetch(`${API}/api/chat/abort`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ conversation_id: conversationId }),
        });
      } catch (e) { /* ignore */ }
    }
    setIsStreaming(false);
    cancelImageGeneration?.();
  };

  const handleSend = async () => {
    if (isStreaming) return;
    if (!message.trim() && attachedFiles.length === 0) {
      toast.error('Veuillez saisir un message');
      return;
    }

    // === SLASH COMMANDS ===
    const trimmed = message.trim();
    if (trimmed.startsWith('/')) {
      const slashCommands = {
        '/resume': async () => {
          if (!conversationId) { toast.error('Aucune conversation a resumer'); return; }
          setIsStreaming(true);
    // Bug 8 fix : timeout 60s max pour éviter spinner infini
    const streamTimeoutRef = setTimeout(() => {
      if (isStreaming) {
        setIsStreaming(false);
        toast.error('Délai dépassé — réessayez');
      }
    }, 60000);
    window._streamTimeout = streamTimeoutRef;
          const priorCount = messages.length;
          setMessages(prev => [...prev, { role: 'user', content: '/resume' }, { role: 'assistant', isSummary: true, summarizing: true, content: '', messageCount: priorCount }]);
          setMessage('');
          try {
            const res = await fetch(`${API}/api/slash/summarize`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ conversation_id: conversationId }) });
            const data = await res.json();
            setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', isSummary: true, summarizing: false, content: data.summary || 'Erreur de resume.', messageCount: priorCount }; return u; });
          } catch { setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', isSummary: true, summarizing: false, content: 'Erreur de connexion.', messageCount: priorCount }; return u; }); }
          clearTimeout(streamTimeoutRef);
          setIsStreaming(false);
        },
        '/pdf': async () => {
          if (!conversationId) { toast.error('Aucune conversation a exporter'); return; }
          window.open(`${API}/api/conversations/${conversationId}/export/pdf?token=${token}`, '_blank');
          setMessage('');
        },
        '/email': async () => {
          const lastMsg = messages.filter(m => m.role === 'assistant').pop();
          if (!lastMsg) { toast.error('Aucun texte a reformater'); return; }
          setIsStreaming(true);
          setMessages(prev => [...prev, { role: 'user', content: '/email' }, { role: 'assistant', content: 'Reformatage en email...' }]);
          setMessage('');
          try {
            const res = await fetch(`${API}/api/slash/reformat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: lastMsg.content, style: 'email' }) });
            const data = await res.json();
            setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: data.result || 'Erreur.' }; return u; });
          } catch { setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: 'Erreur de connexion.' }; return u; }); }
          setIsStreaming(false);
        },
        '/court': async () => {
          const lastMsg = messages.filter(m => m.role === 'assistant').pop();
          if (!lastMsg) { toast.error('Aucun texte a raccourcir'); return; }
          setIsStreaming(true);
          setMessages(prev => [...prev, { role: 'user', content: '/court' }, { role: 'assistant', content: 'Version courte en cours...' }]);
          setMessage('');
          try {
            const res = await fetch(`${API}/api/slash/reformat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: lastMsg.content, style: 'court' }) });
            const data = await res.json();
            setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: data.result || 'Erreur.' }; return u; });
          } catch { setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: 'Erreur de connexion.' }; return u; }); }
          setIsStreaming(false);
        },
        '/formel': async () => {
          const lastMsg = messages.filter(m => m.role === 'assistant').pop();
          if (!lastMsg) { toast.error('Aucun texte a reformuler'); return; }
          setIsStreaming(true);
          setMessages(prev => [...prev, { role: 'user', content: '/formel' }, { role: 'assistant', content: 'Reformulation formelle...' }]);
          setMessage('');
          try {
            const res = await fetch(`${API}/api/slash/reformat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: lastMsg.content, style: 'formel' }) });
            const data = await res.json();
            setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: data.result || 'Erreur.' }; return u; });
          } catch { setMessages(prev => { const u = [...prev]; u[u.length - 1] = { role: 'assistant', content: 'Erreur de connexion.' }; return u; }); }
          setIsStreaming(false);
        },
      };
      const cmd = trimmed.split(' ')[0].toLowerCase();
      if (slashCommands[cmd]) { await slashCommands[cmd](); return; }
    }

    const effectiveMode = imageMode ? 'image' : agentActive ? 'agent' : mode;

    // BYOK mode: check if user has set their API key
    if (effectiveMode === 'byok' && !user?.openai_api_key) {
      setShowByokModal(true);
      return;
    }

    // First-time sync choice is now handled automatically — no blocking prompt
    // Auto-sync can be toggled ON/OFF in Settings → General

    // Agent mode: show confirmation with credit estimate
    if (effectiveMode === 'agent' && !pendingAgentMessage) {
      setPendingAgentMessage(message);
      setShowAgentConfirm(true);
      return;
    }

    // Reset pending agent message after confirmation
    if (pendingAgentMessage) setPendingAgentMessage(null);

    // File info: short display for user message (no extracted content)
    const fileDisplayInfo = attachedFiles.length > 0
      ? attachedFiles.map(f => {
          const icon = f.ext === '.zip' ? '📦' : f.ext === '.pdf' ? '📄' : f.ext?.match(/docx?/) ? '📝' : f.ext?.match(/xlsx?/) ? '📊' : '📎';
          return `${icon} ${f.name}`;
        }).join('\n')
      : '';
    // Full file context sent to AI (hidden from display)
    const fileContextForAI = attachedFiles.length > 0
      ? attachedFiles.map(f => {
          return f.extracted_text ? `[Fichier: ${f.name}]\n${f.extracted_text.slice(0, 3000)}` : '';
        }).filter(Boolean).join('\n\n')
      : '';
    const displayContent = message + (fileDisplayInfo ? '\n' + fileDisplayInfo : '');
    const userMsg = { role: 'user', content: displayContent, files: attachedFiles.length > 0 ? attachedFiles : undefined, mode: effectiveMode, fileContext: fileContextForAI };
    setMessages(prev => [...prev, userMsg]);
    const sentFiles = [...attachedFiles];
    const sentMessage = message.trim() || (sentFiles.length > 0 ? 'Analyse ce fichier' : '');
    setMessage('');
    setAttachedFiles([]);
      // Bug 20 fix : nettoyer les fichiers temporaires côté serveur
      try {
        attachedFiles.forEach(f => {
          if (f.serverId) fetch(`${API}/api/uploads/${f.serverId}`, {
            method: 'DELETE', headers: { Authorization: `Bearer ${token}` }
          }).catch(() => {});
        });
      } catch (e) { /* silencieux */ }
    if (onFilesChange) onFilesChange([]);
    setIsStreaming(true);
    let capturedConversationId = conversationId;

    // === CUSTOM AGENT MODE: route to custom agent API ===
    if (selectedAgent) {
      try {
        const agentRes = await fetch(`${API}/api/custom-agents/${selectedAgent.id}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ message: sentMessage + (fileContextForAI ? '\n\n' + fileContextForAI : '') }),
        });
        const data = await agentRes.json();
        if (data.success) {
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.response,
            agentName: selectedAgent.name,
            agentColor: selectedAgent.color,
          }]);
        } else {
          setMessages(prev => [...prev, { role: 'assistant', content: data.detail || 'Erreur de l\'agent.' }]);
          toast.error(data.detail || 'Erreur');
        }
      } catch (err) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Erreur de connexion avec l\'agent.' }]);
      }
      setIsStreaming(false);
      return;
    }

    // === AGENT MODE: WebSocket with Browser-Use ===
    if (effectiveMode === 'agent') {
      try {
        // First, create conversation via regular endpoint to get conversation_id
        const initRes = await fetch(`${API}/api/chat/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ message: sentMessage, mode: 'agent', conversation_id: conversationId })
        });
        // Read SSE to get conversation_id
        const reader = initRes.body.getReader();
        const decoder = new TextDecoder();
        let initContent = '';
        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.content) {
                  initContent += data.content;
                  const _vis = initContent
                    .replace(/\[GENERATE_FILE:[^\]]*\][\s\S]*?\[\/GENERATE_FILE\]/g, '')
                    .replace(/\[CORRECTED_FILE:[^\]]*\][\s\S]*?\[\/CORRECTED_FILE\]/g, '')
                    .replace(/^(Je vais |Voici |Bien sûr|D'accord|Parfait,|Voici une version)[^\n]*/gm, '')
                    .trim();
                  setMessages(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { role: 'assistant', content: _vis || initContent };
                    return updated;
                  });
                }
                if (data.conversation_id) {
                  capturedConversationId = data.conversation_id;
                  setConversationId(data.conversation_id);
                  // Rafraîchir la liste de conversations (onglet sidebar) dès réception
                  if (!conversationId && window.__refreshConversations) {
                    window.__refreshConversations();
                  }
                }
              } catch (e) { /* silencieux */ }
            }
          }
        }

        // Now start WebSocket Browser-Use agent
        const wsProtocol = API.startsWith('https') ? 'wss' : 'ws';
        const wsHost = API.replace(/^https?:\/\//, '');
        const wsUrl = `${wsProtocol}://${wsHost}/api/ws/agent`;

        const ws = new WebSocket(wsUrl);
        agentWsRef.current = ws; // Store ref for cancellation
        let agentContent = initContent || '';

        // Initialize Manus IA-style animated steps
        setAgentSteps([{ type: 'init', message: 'Initialisation de l\'agent...', status: 'active', timestamp: Date.now() }]);

        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: agentContent, isAgent: true };
          return updated;
        });

        ws.onopen = async () => {
          // Tenter de récupérer le contenu de la page active
          // via l'extension Chrome si disponible
          let pageContext = "";
          let pageUrl = "";
          try {
            if (typeof chrome !== 'undefined' && chrome.runtime?.id) {
              const pageData = await new Promise((resolve) => {
                chrome.runtime.sendMessage({ type: "GET_PAGE_CONTENT" }, (r) => {
                  if (chrome.runtime.lastError) { resolve({}); return; }
                  resolve(r || {});
                });
              });
              if (pageData.content && pageData.url?.startsWith("http")) {
                pageContext = pageData.content.slice(0, 3000);
                pageUrl = pageData.url;
              }
            }
          } catch (e) { /* silencieux */ }
          ws.send(JSON.stringify({
            task: sentMessage,
            token,
            conversation_id: capturedConversationId,
            extracted_content: pageContext,
            navigated_url: pageUrl
          }));
          setAgentSteps(prev => [
            { ...prev[0], status: 'done' },
            { type: 'connect', message: 'Connexion établie, lancement de la tâche...', status: 'active', timestamp: Date.now() }
          ]);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'step') {
              const stepMsg = data.message + (data.url ? ` → ${data.url}` : '');
              agentContent += `\n- ${data.message}`;
              if (data.url) agentContent += ` (${data.url})`;
              agentContent += '\n';
              setAgentSteps(prev => {
                const updated = prev.map(s => s.status === 'active' ? { ...s, status: 'done' } : s);
                return [...updated, { type: 'step', message: stepMsg, status: 'active', timestamp: Date.now() }];
              });
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: agentContent, isAgent: true };
                return updated;
              });
            } else if (data.type === 'progress') {
              agentContent += `\n_${data.message}_\n`;
              setAgentSteps(prev => {
                const updated = prev.map(s => s.status === 'active' ? { ...s, status: 'done' } : s);
                return [...updated, { type: 'progress', message: data.message, status: 'active', timestamp: Date.now() }];
              });
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: agentContent, isAgent: true };
                return updated;
              });
            } else if (data.type === 'result') {
              // Son de complétion (comme Manus IA)
              try {
                const ctx = new AudioContext();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.type = 'sine'; osc.frequency.value = 880;
                gain.gain.setValueAtTime(0.3, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
                osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.5);
              } catch (e) { /* silencieux */ }
              agentContent += `\n---\n\n${data.content}`;
              setAgentSteps(prev => {
                const updated = prev.map(s => ({ ...s, status: 'done' }));
                return [...updated, { type: 'result', message: 'Tâche terminée avec succès', status: 'done', timestamp: Date.now() }];
              });
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: agentContent, isAgent: true, credit_cost: data.credits_used || 0 };
                return updated;
              });
              setTotalCreditsUsed(prev => prev + (data.credits_used || 0));
              // FIX CRÉDITS: refreshUser resynchronise tous les buckets depuis le serveur
              // au lieu d'un calcul optimiste qui faussait l'affichage multi-buckets
              if (refreshUser) refreshUser();
              setIsStreaming(false);
              setTimeout(() => setAgentSteps([]), 3000);
              
              ws.close();
            } else if (data.type === 'error') {
              agentContent += `\n\n**Erreur:** ${data.message}`;
              setAgentSteps(prev => [
                ...prev.map(s => ({ ...s, status: 'done' })),
                { type: 'error', message: data.message, status: 'error', timestamp: Date.now() }
              ]);
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: agentContent, isAgent: false };
                return updated;
              });
              setIsStreaming(false);
              setTimeout(() => setAgentSteps([]), 3000);
              ws.close();
            }
          } catch (e) { /* silencieux */ }
        };

        ws.onerror = () => {
          agentContent += '\n\n**Erreur de connexion WebSocket.**';
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: agentContent };
            return updated;
          });
          setIsStreaming(false);
        };

        ws.onclose = () => {
          setIsStreaming(false);
        };

      } catch (err) {
        const errMsg = err?.message || String(err);
        let userFriendlyError = "Erreur de connexion a l'Agent IA.";
        if (errMsg.includes('TCPTransport') || errMsg.includes('handler is closed')) {
          userFriendlyError = "L'agent IA a ete interrompu. Rechargez la page et reessayez.";
        } else if (errMsg.includes('401') || errMsg.includes('token')) {
          userFriendlyError = "Session expiree. Veuillez vous reconnecter.";
        } else if (errMsg.includes('402') || errMsg.includes('crédit')) {
          userFriendlyError = "Credits insuffisants pour l'Agent IA (50 credits requis).";
        } else if (errMsg.includes('timeout') || errMsg.includes('TimeoutError')) {
          userFriendlyError = "Delai depasse. La tache etait trop longue. Essayez une demande plus courte.";
        } else if (errMsg.includes('Failed to fetch') || errMsg.includes('network')) {
          userFriendlyError = "Probleme de reseau. Verifiez votre connexion internet.";
        }
        setMessages(prev => [...prev, { role: 'assistant', content: userFriendlyError }]);
        setIsStreaming(false);
      }
      return;
    }

    // === REGULAR MODE: SSE Stream ===
    let progressInterval = null;
    let assistantContent = ''; // Declare outside try block for finally access
    try {
      // Include file context in the message sent to AI (invisible to user)
      const messageForAI = fileContextForAI 
        ? fileContextForAI + "\n\nMessage utilisateur: " + sentMessage 
        : sentMessage;
      const body = {
        message: messageForAI,
        mode: effectiveMode,
        conversation_id: conversationId,
        file_ids: sentFiles.map(f => f.id).filter(Boolean),
      };
      if (imageMode) body.image_model = imageModel;

      // Start image progress animation
      if (imageMode) {
        startImageGeneration?.(conversationId, imageModel, sentMessage);
      }

      // Create AbortController for stop button
      const abortController = new AbortController();
      abortStreamingRef.current = abortController;

      const response = await fetch(`${API}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      });

      if (!response.ok) {
        let errMsg = 'Erreur serveur. Veuillez reessayer.';
        try { const errData = await response.json(); errMsg = errData.detail || errMsg; } catch {}
        setMessages(prev => [...prev, { role: 'assistant', content: errMsg }]);
        setIsStreaming(false);
        if (progressInterval) { clearInterval(progressInterval); cancelImageGeneration?.(); }
        return;
      }

      // Clone response before reading body to prevent Chrome extension conflicts
      const streamResponse = response.clone();
      const reader = streamResponse.body.getReader();
      const decoder = new TextDecoder();
      assistantContent = ''; // Reset for this request
      let sseBuffer = ''; // Buffer for partial SSE lines (critical for large image base64 data)

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      const processSSELine = (line) => {
        if (!line.startsWith('data: ')) return;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content) {
            assistantContent += data.content;
              // Masquer les blocs techniques [CORRECTED_FILE] pendant le stream
              const _visContent = assistantContent
                .replace(/\[CORRECTED_FILE:[^\]]*\][\s\S]*?\[\/CORRECTED_FILE\]/g, '')
                .replace(/\[GENERATE_FILE:[^\]]*\][\s\S]*?\[\/GENERATE_FILE\]/g, '')
                .replace(/\[CORRECTED_FILE:[^\]]*\][\s\S]*/g, '\n*⏳ Correction en cours...*')
                .replace(/^(Je vais |Voici |Bien sûr|D'accord|Parfait,|Voici une version)[^\n]*/gm, '')
                .trim();
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: 'assistant', content: _visContent || assistantContent };
                return updated;
              });
          }
          // Mise à jour finale nettoyée envoyée par le backend
          if (data.display_update) {
            // Mettre à jour l'accumulateur pour que les références ultérieures utilisent le texte propre
            assistantContent = data.display_update;
            const _clean = data.display_update
              .replace(/^(Je vais |Voici |Bien sûr|D'accord|Parfait,|Voici une version)[^\n]*/gm, '')
              .trim();
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = { ...updated[updated.length - 1], content: _clean || data.display_update };
              return updated;
            });
          }
          if (data.file_download) {
            const { url, filename, format: fmt, corrected_files, size } = data.file_download;
            const dlToken = localStorage.getItem('zayado_token');
            const fullUrl = `${API}${url}${url.includes('?') ? '&' : '?'}token=${dlToken}`;
            // FIX MESSAGES — Ajouter download au message COURANT (pas setMessages qui cause re-render)
            // et forcer sauvegarde de la conversation avant d'ouvrir
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = { ...updated[updated.length - 1] };
              if (!lastMsg.downloads) lastMsg.downloads = [];
              // Éviter les doublons
              const already = lastMsg.downloads.some(d => d.filename === filename);
              if (!already) {
                lastMsg.downloads.push({ url: fullUrl, filename, format: fmt, corrected_files, size });
              }
              updated[updated.length - 1] = lastMsg;
              return updated;
            });
            // FIX — Sauvegarder la conversation en DB (fire-and-forget, sans await)
            if (capturedConversationId) {
              fetch(`${API}/api/chat/conversations/${capturedConversationId}/touch`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` }
              }).catch(() => {}); // fire-and-forget intentionnel
            }
          }
          if (data.conversation_id) {
            const isNew = !capturedConversationId;
            capturedConversationId = data.conversation_id;
            setConversationId(data.conversation_id);
            if (!conversationCreatedAt) setConversationCreatedAt(new Date().toISOString());
            // Rafraîchir la liste des conversations dans la sidebar dès qu'une nouvelle conversation est créée
            if (isNew && window.__refreshConversations) {
              window.__refreshConversations();
            }
          }
          if (data.credits_used) {
            setTotalCreditsUsed(prev => prev + data.credits_used);
          }
          // FIX CRÉDITS : mettre à jour le credit_cost du dernier message utilisateur
          // avec le vrai décompte venant du backend (pas l'estimation initiale)
          if (data.credit_update) {
            setMessages(prev => {
              const updated = [...prev];
              // Trouver le dernier message utilisateur et corriger son credit_cost
              for (let i = updated.length - 1; i >= 0; i--) {
                if (updated[i].role === 'user') {
                  updated[i] = { ...updated[i], credit_cost: data.credit_update };
                  break;
                }
              }
              return updated;
            });
            setTotalCreditsUsed(prev => {
              // Remplacer l'estimation par le vrai montant
              return prev + data.credit_update;
            });
          }
          // Gestion des erreurs backend (crédits insuffisants, erreur IA, etc.)
          if (data.error) {
            const errMsg = data.error || 'Une erreur est survenue. Veuillez réessayer.';
            const isCreditsError = errMsg.toLowerCase().includes('credits insuf') || errMsg.toLowerCase().includes('crédit');
            setMessages(prev => {
              const updated = [...prev];
              if (isCreditsError) {
                updated[updated.length - 1] = {
                  role: 'assistant',
                  content: `Il semblerait que vous ayez épuisé tous vos crédits. Pas de souci ! Ajoutez simplement plus de crédits à votre compte et poursuivez.`,
                  credits_exhausted: true
                };
              } else {
                updated[updated.length - 1] = { role: 'assistant', content: `⚠️ **Erreur :** ${errMsg}` };
              }
              return updated;
            });
            setIsStreaming(false);
            if (progressInterval) clearInterval(progressInterval);
          }
          if (data.done) {
            // FIX CRÉDITS: on ne touche plus user.credits directement.
            // remaining_credits du backend = total des 3 buckets. L'écraser dans
            // user.credits seul ferait afficher un solde gonflé (sidebar additionne les 3).
            // refreshUser() rappelle /api/auth/me et resynchronise tous les buckets.
            let actualCreditsUsed = data.credits_used || { fast: 2, pro: 4, gemini: 3, grok: 3, perplexity: 4, image: 8, agent: 0 }[effectiveMode] || 0;
            if (effectiveMode !== 'byok' && refreshUser) {
              refreshUser();
            }
            // Trigger notification for image generation
            if (effectiveMode === 'image') {
              notifyTaskComplete('image', { creditsUsed: actualCreditsUsed });
              setTaskCompleteData({ taskType: 'image', message: 'Image générée avec succès', creditsUsed: actualCreditsUsed });
              setShowTaskComplete(true);
            }
          }
        } catch { /* partial JSON, will be completed in next chunk */ }
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            // Process any remaining buffered data
            if (sseBuffer.trim()) processSSELine(sseBuffer.trim());
            break;
          }

          sseBuffer += decoder.decode(value, { stream: true });
          // Split on double newline (SSE event separator) to handle large payloads correctly
          const events = sseBuffer.split('\n\n');
          // Keep the last part as buffer (may be incomplete)
          sseBuffer = events.pop() || '';
          for (const event of events) {
            const lines = event.split('\n');
            for (const line of lines) {
              if (line.trim()) processSSELine(line);
            }
          }
        }
      } catch (streamErr) {
        console.warn('Stream interrupted:', streamErr.message);
        // Try to process remaining buffer
        if (sseBuffer.trim()) processSSELine(sseBuffer.trim());
        if (assistantContent) {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: 'assistant', content: assistantContent };
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Erreur de connexion. Veuillez reessayer.' }]);
    } finally {
      setIsStreaming(false);
      if (progressInterval) { clearInterval(progressInterval); }
      // Hide image animation only after image content is received
      if (imageMode) {
        completeImageGeneration?.(true);
      } else {
        cancelImageGeneration?.();
      }
      // If agent mode, start polling — use capturedConversationId (local, always up to date)
      if (effectiveMode === 'agent' && capturedConversationId) {
        setConversationId(capturedConversationId);
        setManusPolling(true);
      }
      // ── Sync auto cloud ──────────────────────────────────────
      // Only sync when AI has responded, and include both user message + AI response
      if (assistantContent) {
        const autoSyncEnabled = localStorage.getItem('zayado_autosync_enabled') !== 'false'; // default ON
        let syncSource = safeLocalGet('zayado_autosync_source')
          else if (driveConnected.onedrive) { syncSource = 'onedrive'; localStorage.setItem('zayado_autosync_source', 'onedrive'); }
        }
        if (autoSyncEnabled && syncSource !== 'none') {
          setAutoSyncing(true);
          try {
            // SYNC CONVERSATION COMPLÈTE — 1 fichier par conversation, mis à jour à chaque échange
            // Plus jamais de doublon : le fichier est identifié par conversation_id
            const doSync = async () => {
              const currentMessages = [...messages];
              // Ajouter le dernier échange si pas encore dans messages
              const allMsgs = currentMessages;
              
              if (syncSource === 'gdrive') {
                await fetch(`${API}/api/drive/sync-conversation`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                  body: JSON.stringify({
                    conversation_id: capturedConversationId || conversationId || `conv_${Date.now()}`,
                    title: allMsgs.find(m => m.role === 'user')?.content?.slice(0, 50) || 'Conversation',
                    messages: allMsgs.filter(m => m.role !== 'system' && !m.isAgentSwitch),
                  })
                });
              } else if (syncSource === 'onedrive' || syncSource === 'sharepoint') {
                // OneDrive : même approche, 1 fichier par conversation
                const ts = new Date().toISOString().slice(0, 10);
                const convIdShort = (capturedConversationId || conversationId || 'unknown').slice(0, 8);
                const filename = `conversation_${ts}_${convIdShort}.md`;
                const lines = ['# Conversation Extension IA', ''];
                allMsgs.filter(m => m.role !== 'system').forEach(m => {
                  lines.push(m.role === 'user' ? `**Vous :** ${m.content}` : `**Extension IA :** ${m.content}`);
                  lines.push('');
                });
                const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
                const form = new FormData();
                form.append('file', blob, filename);
                await fetch(`${API}/api/onedrive/upload?folder_path=Extension%20IA%2FConversations`, {
                  method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form
                });
              }
              const now = new Date().toLocaleString('fr-FR');
              localStorage.setItem('zayado_last_sync_time', now);
              setLastSyncTime(now);
              setAutoSyncing(false);
              // Notification toast à la première sync auto (RGPD + transparence)
              if (!localStorage.getItem('zayado_sync_notified') {
                localStorage.setItem('zayado_sync_notified', 'true');
                const providerLabel = syncSource === 'gdrive' ? 'Google Drive' : syncSource === 'onedrive' ? 'OneDrive' : 'SharePoint';
                toast.success(
                  React.createElement('div', { className: 'flex flex-col gap-0.5' },
                    React.createElement('span', null, `✅ Sauvegardé sur ${providerLabel} automatiquement`),
                    React.createElement('button', {
                      className: 'text-xs underline text-left opacity-80 hover:opacity-100',
                      onClick: () => window.dispatchEvent(new CustomEvent('openSettings', { detail: { tab: 'stockage' } }))
                    }, 'Modifier les préférences de sync →')
                  ),
                  { duration: 6000 }
                );
              }
            };
            doSync().catch(() => setAutoSyncing(false));
          } catch { setAutoSyncing(false); }
        }
      }
      // ────────────────────────────────────────────────────────
    }
  };

  const handleKeyDown = (e) => {
    // Navigation clavier dans le menu slash commands
    if (showSlashMenu) {
      const slashQuery = message.startsWith('/') ? message : '/';
      const filtered = SLASH_COMMANDS.filter(c =>
        c.cmd.startsWith(slashQuery.toLowerCase()) || c.label.toLowerCase().includes(slashQuery.slice(1).toLowerCase())
      );
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSlashActiveIdx(prev => Math.min(prev + 1, filtered.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSlashActiveIdx(prev => Math.max(prev - 1, 0));
        return;
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (filtered[slashActiveIdx]) {
          setMessage(filtered[slashActiveIdx].cmd);
          setShowSlashMenu(false);
          setSlashActiveIdx(0);
          inputRef.current?.focus();
        }
        return;
      }
      if (e.key === 'Escape') {
        setShowSlashMenu(false);
        setSlashActiveIdx(0);
        return;
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-send for quick prompts: when message is set and matches pending ref, trigger send
  useEffect(() => {
    if (pendingAutoSendRef.current && message === pendingAutoSendRef.current && !isStreaming) {
      pendingAutoSendRef.current = null;
      handleSend();
    }
  }, [message]);

  // Auto-resize textarea up to 5 lines
  useEffect(() => {
    if (!inputRef.current) return;
    const el = inputRef.current;
    el.style.height = 'auto';
    const lineHeight = 24;
    const maxHeight = lineHeight * 5;
    el.style.height = Math.min(el.scrollHeight, maxHeight) + 'px';
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
  }, [message]);

  // Listen for screenshot trigger from header
  useEffect(() => {
    const handler = () => { if (fileInputRef.current) fileInputRef.current.click(); };
    window.addEventListener('zayado-screenshot-trigger', handler);
    return () => window.removeEventListener('zayado-screenshot-trigger', handler);
  }, []);

  // Close plus menu on outside click
  useEffect(() => {
    if (!showPlusMenu) return;
    const handler = (e) => { if (plusMenuRef.current && !plusMenuRef.current.contains(e.target)) setShowPlusMenu(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showPlusMenu]);

  // Fetch custom prompts for the dropdown
  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/prompts`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          const sys = data.system_prompts || [];
          const usr = data.user_prompts || [];
          setSystemPrompts(sys);
          setUserPrompts(usr);
          setPromptsList([...sys, ...usr]);
        }
      })
      .catch(() => {});
  }, [token]);

  // Save a new user prompt
  const saveNewPrompt = async () => {
    if (!newPromptTitle.trim() || !newPromptText.trim()) return;
    setSavingPrompt(true);
    try {
      const res = await fetch(`${API}/api/prompts`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newPromptTitle.trim(), prompt: newPromptText.trim(), action: newPromptAction, category: 'custom' })
      });
      if (res.ok) {
        const created = await res.json();
        const updated = [...userPrompts, created];
        setUserPrompts(updated);
        setPromptsList([...systemPrompts, ...updated]);
        setNewPromptTitle(''); setNewPromptText(''); setNewPromptAction('insert');
        setShowAddPrompt(false);
        toast.success('Prompt ajouté');
      }
    } catch (e) { /* silencieux */ }
    setSavingPrompt(false);
  };

  // Close prompts dropdown on outside click
  useEffect(() => {
    if (!showPromptsDropdown) return;
    const handler = (e) => {
      if (!e.target.closest('[data-testid="prompts-dropdown-wrapper"]') && !e.target.closest('[data-testid="prompts-dropdown-wrapper-empty"]')) setShowPromptsDropdown(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showPromptsDropdown]);

  // Close agent picker on outside click
  useEffect(() => {
    if (!showAgentPicker) return;
    const handler = (e) => {
      if (!e.target.closest('[data-testid="agent-picker-dropdown"]') && !e.target.closest('[data-testid="agent-picker-conv"]') && !e.target.closest('[data-testid="agent-toggle-btn"]') && !e.target.closest('[data-testid="agent-toggle-btn-empty"]'))
        setShowAgentPicker(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showAgentPicker]);

  const toggleAgentPicker = () => {
    if (!showAgentPicker && agentToggleRef.current) {
      const rect = agentToggleRef.current.getBoundingClientRect();
      setAgentPickerPos({ top: rect.top, left: rect.right - 224 });
    }
    setShowAgentPicker(prev => !prev);
  };

  // Screen capture function
  const handleScreenCapture = async () => {
    setShowPlusMenu(false);
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' } });
      const video = document.createElement('video');
      video.srcObject = stream;
      await video.play();
      await new Promise(r => setTimeout(r, 300));
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      stream.getTracks().forEach(t => t.stop());
      canvas.toBlob(async (blob) => {
        if (!blob) return toast.error('Erreur de capture');
        const file = new File([blob], `capture-${Date.now()}.png`, { type: 'image/png' });
        setMessage('Analyse cette capture d\'ecran et donne-moi des recommandations detaillees.');
        // Upload the capture
        const formData = new FormData();
        formData.append('file', file);
        setUploadingFile(true);
        try {
          const res = await fetch(`${API}/api/chat/upload`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData });
          if (res.ok) {
            const data = await res.json();
            setAttachedFiles(prev => [...prev, { name: file.name, url: data.url || data.file_url, extracted_text: data.extracted_text || '', size: file.size }]);
            toast.success('Capture ajoutee');
          } else { toast.error('Erreur upload capture'); }
        } catch { toast.error('Erreur upload capture'); }
        setUploadingFile(false);
        inputRef.current?.focus();
      }, 'image/png');
    } catch (err) {
      if (err.name !== 'AbortError') toast.error('Capture annulee ou non supportee');
    }
  };

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
  };

  // Sync drive handler
  const handleSyncDrive = async () => {
    setSyncingDrive(true);
    try {
      const syncSource = safeLocalGet('zayado_autosync_source')/api/drive/sync`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
        synced = true;
      } else if (syncSource === 'onedrive' || (syncSource === 'none' && driveConnected.onedrive)) {
        await fetch(`${API}/api/onedrive/sync`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
        synced = true;
      } else if (syncSource === 'sharepoint') {
        const siteId = safeLocalGet('zayado_sp_site_id')/api/onedrive/sharepoint/sync/${siteId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
          synced = true;
        }
      }
      if (synced) {
        const now = new Date().toLocaleString('fr-FR');
        localStorage.setItem('zayado_last_sync_time', now);
        setLastSyncTime(now);
        toast.success('Synchronisation terminee');
      } else {
        toast.error('Connectez votre Drive dans Paramètres → Drive Pro');
      }
    } catch {
      toast.error('Erreur de synchronisation');
    }
    setSyncingDrive(false);
  };

  const currentMode = imageMode
    ? { id: 'image', label: 'Image IA', icon: Image }
    : [...modes, ...extras].find(m => m.id === mode) || { id: 'image', label: 'Image IA', icon: Image };

  // Empty state (no messages yet)
  if (messages.length === 0) {
    const currentQuickCat = quickPromptCats.find(c => c.id === quickCat);
    return (
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 overflow-hidden min-h-0" data-testid="chat-empty-state">
        {/* Mode bar — same as conversation mode bar */}
        <div className="border-b border-[#E5E5E5] dark:border-gray-700 px-4 py-2 flex items-center justify-between bg-white dark:bg-gray-900 shrink-0 overflow-x-auto">
          <div className="flex items-center gap-1 shrink-0">
            {imageMode ? (
              <div className="flex items-center gap-2" data-testid="image-mode-bar-empty">
                <div className="flex items-center gap-2 bg-[#E8F4F8] border border-[#1D4E8A]/20 rounded-lg px-3 py-1.5">
                  <Image className="w-4 h-4 text-[#1D4E8A]" />
                  <span className="text-xs font-bold text-[#1D4E8A]">Mode Image IA</span>
                  <span className="text-[10px] text-[#1D4E8A]/60">8 credits/image</span>
                </div>
                <div className="flex items-center gap-0.5 bg-white/60 dark:bg-gray-800 rounded-lg p-0.5">
                  {imageModels(lang).map(im => (
                    <button key={im.id} onClick={() => setImageModel(im.id)}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${imageModel === im.id ? 'bg-white dark:bg-gray-700 shadow-sm text-[#1D4E8A]' : 'text-gray-500 hover:text-gray-700'}`}
                      data-testid={`image-model-empty-${im.id}`}>
                      <span>{im.label}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${imageModel === im.id ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'bg-gray-200 text-gray-500'}`}>{im.badge}</span>
                    </button>
                  ))}
                </div>
                <button onClick={() => setImageMode(false)} className="p-1.5 hover:bg-gray-200 rounded-lg text-gray-400 hover:text-gray-600" data-testid="exit-image-mode-empty" title="Quitter le mode Image">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <>
                {/* === MOBILE : dropdown compact style ChatGPT === */}
                <div className="relative sm:hidden" data-testid="mobile-mode-dropdown-empty">
                  <button
                    onClick={() => setShowExtraModes(!showExtraModes)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 bg-white text-xs font-semibold text-gray-800 shadow-sm"
                    data-testid="mobile-mode-btn-empty"
                  >
                    {React.createElement(currentMode.icon, { className: 'w-3.5 h-3.5 text-[#1D4E8A]' })}
                    <span>{currentMode.label}</span>
                    <ChevronDown className="w-3 h-3 text-gray-400" />
                  </button>
                  {showExtraModes && (
                    <div className="fixed inset-0 z-[200]" onClick={() => setShowExtraModes(false)}>
                      <div className="fixed left-4 right-4 bottom-[45vh] bg-white border border-gray-200 rounded-xl shadow-2xl z-[201] py-1 max-h-[50vh] overflow-y-auto" data-testid="mobile-mode-menu-empty" onClick={e => e.stopPropagation()}>
                      {modes.map(m => {
                        const Icon = m.icon;
                        return (
                          <button key={m.id}
                            onClick={() => { handleModeChange(m.id); setShowExtraModes(false); }}
                            className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors ${
                              mode === m.id ? 'bg-[#1D4E8A]/8 text-[#1D4E8A] font-semibold' : 'text-gray-700 hover:bg-gray-50'
                            }`}
                            data-testid={`mobile-mode-item-empty-${m.id}`}
                          >
                            <Icon className={`w-4 h-4 ${mode === m.id ? 'text-[#1D4E8A]' : 'text-gray-400'}`} />
                            <div className="flex-1 text-left">
                              <div className="font-medium">{m.label}</div>
                              <div className="text-[10px] text-gray-400">{m.desc}</div>
                            </div>
                            {mode === m.id && <Check className="w-3.5 h-3.5 text-[#1D4E8A]" />}
                          </button>
                        );
                      })}
                      <div className="border-t border-gray-100 mt-1 pt-1">
                        <button
                          onClick={() => { setImageMode(true); setImageModel('nano-banana'); setShowExtraModes(false); }}
                          className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                          <Image className="w-4 h-4 text-gray-400" />
                          <div className="flex-1 text-left">
                            <div className="font-medium">Image IA</div>
                            <div className="text-[10px] text-gray-400">Génération d'images · 8 crédits</div>
                          </div>
                        </button>
                      </div>
                    </div>
                    </div>
                  )}
                </div>
                {/* === DESKTOP : tabs normaux === */}
                <div className="hidden sm:flex items-center gap-0.5 bg-white/60 dark:bg-gray-800 rounded-lg p-0.5">
                  {modes.map((m, idx) => {
                    const Icon = m.icon;
                    return (
                      <React.Fragment key={m.id}>
                        <button onClick={() => handleModeChange(m.id)}
                          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                            m.isAgent
                              ? (mode === m.id ? 'bg-orange-600 text-white shadow-sm' : 'text-orange-600 hover:bg-orange-50 border border-orange-200')
                              : (mode === m.id ? 'bg-[#1D4E8A] text-white shadow-sm' : 'text-[#1D4E8A]/70 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5')
                          }`}
                          data-testid={`mode-tab-empty-${m.id}`} title={`${m.label} — ${m.desc}`}>
                          <Icon className={`w-3.5 h-3.5 ${mode === m.id ? 'text-white' : m.isAgent ? 'text-orange-500' : 'text-[#1D4E8A]/60'}`} />
                          <span>{m.label}</span>
                          {m.isAgent && <span className="text-[9px] px-1 py-0.5 rounded bg-orange-100 text-orange-600 ml-0.5 font-bold">AUTO</span>}
                        </button>
                        {m.separator_after && <div className="w-px h-5 bg-gray-200 mx-0.5 flex-shrink-0" />}
                      </React.Fragment>
                    );
                  })}
                </div>
                <div className="hidden sm:block w-px h-5 bg-gray-200 mx-0.5 flex-shrink-0" />
                <button onClick={() => { setImageMode(!imageMode); if (!imageMode) setImageModel('nano-banana'); }}
                  className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${imageMode ? 'bg-[#1D4E8A] text-white shadow-sm' : 'text-[#1D4E8A]/70 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5'}`}
                  data-testid="toggle-image-mode-empty" title="Mode Image IA">
                  <Image className={`w-3.5 h-3.5 ${imageMode ? 'text-white' : 'text-[#1D4E8A]/60'}`} />
                  <span>Image</span>
                </button>
              </>
            )}
          </div>
          <div className="flex items-center gap-1">
            {/* New conversation button */}
            <button onClick={() => { navigate('/app'); window.location.reload(); }}
              className="p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 text-[#1D4E8A]/60 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5"
              data-testid="new-conv-btn-empty" title="Nouvelle conversation">
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline text-[10px]">Nouveau</span>
            </button>
            {/* Screenshot mode button */}
            <button onClick={handleScreenCapture}
              className="p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 text-[#1D4E8A]/60 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5"
              data-testid="screenshot-btn-empty" title="Capturer l'ecran">
              <Camera className="w-3.5 h-3.5" />
              <span className="hidden sm:inline text-[10px]">Screenshot</span>
            </button>
          </div>
        </div>

        {/* Scrollable content area */}
        <div className="flex-1 flex flex-col items-center px-3 sm:px-4 pt-4 sm:pt-8 pb-2 sm:pb-4 overflow-y-auto relative">
          {/* Salutation personnalisée + widgets métier */}
          <div className="mb-3 sm:mb-6 w-full max-w-2xl">
            {/* Salutation */}
            <div className="mb-2 sm:mb-4">
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2" style={{ fontFamily: 'Manrope, sans-serif', lineHeight: 1.2 }}>
                Bonjour{user?.name ? ', ' + user.name.split(' ')[0] : ''} 👋
              </h1>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                {user?.settings?.metier || 'Indépendant'} — que voulez-vous accomplir aujourd'hui ?
              </p>
            </div>

            {/* Widgets contextuels (affichés uniquement si données disponibles) */}
            {(serenityScore !== null || activeTimer) && (
              <div className="flex flex-wrap gap-3 mb-4" data-testid="welcome-widgets">
                {/* Score sérénité — carte premium */}
                {serenityScore !== null && (
                  <button
                    className={`group flex items-center gap-3 px-4 py-3 rounded-2xl border-2 cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:shadow-lg text-left ${
                      serenityScore >= 70
                        ? 'bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200 hover:border-emerald-300'
                        : serenityScore >= 40
                        ? 'bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200 hover:border-amber-300'
                        : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200 hover:border-red-300'
                    }`}
                    title="Cliquer pour analyser ma situation financière"
                    data-testid="widget-serenity"
                    onClick={() => { setMessage('Analyse ma situation financière et donne-moi des recommandations'); inputRef.current?.focus(); }}
                  >
                    {/* Jauge circulaire */}
                    <div className="relative w-10 h-10 shrink-0">
                      <svg viewBox="0 0 36 36" className="w-10 h-10 -rotate-90">
                        <circle cx="18" cy="18" r="15" fill="none" stroke="#E5E7EB" strokeWidth="3" />
                        <circle cx="18" cy="18" r="15" fill="none"
                          stroke={serenityScore >= 70 ? '#059669' : serenityScore >= 40 ? '#D97706' : '#DC2626'}
                          strokeWidth="3"
                          strokeDasharray={`${(serenityScore / 100) * 94.2} 94.2`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-black" style={{ color: serenityScore >= 70 ? '#059669' : serenityScore >= 40 ? '#D97706' : '#DC2626' }}>
                        {serenityScore}
                      </span>
                    </div>
                    <div>
                      <div className={`text-[11px] font-semibold uppercase tracking-wide ${
                        serenityScore >= 70 ? 'text-emerald-600' : serenityScore >= 40 ? 'text-amber-600' : 'text-red-600'
                      }`}>Sérénité financière</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {serenityScore >= 70 ? 'Situation saine ✓' : serenityScore >= 40 ? 'À surveiller' : 'Action requise'}
                      </div>
                    </div>
                  </button>
                )}

                {/* Timer actif — carte premium */}
                {activeTimer && (
                  <button
                    className="group flex items-center gap-3 px-4 py-3 rounded-2xl border-2 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 hover:border-blue-300 cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:shadow-lg text-left"
                    title="Cliquer pour voir l'avancement du projet"
                    data-testid="widget-timer"
                    onClick={() => { setMessage(`Montre-moi l'avancement du projet ${activeTimer.name}`); inputRef.current?.focus(); }}
                  >
                    <div className="w-10 h-10 rounded-full bg-blue-100 border-2 border-blue-200 flex items-center justify-center shrink-0">
                      <span className="text-lg animate-pulse">⏱️</span>
                    </div>
                    <div>
                      <div className="text-[11px] font-semibold uppercase tracking-wide text-blue-600">Timer actif</div>
                      <div className="text-xs text-gray-600 font-medium mt-0.5 truncate max-w-[130px]">{activeTimer.name}</div>
                    </div>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* ─── SUGGESTIONS RAPIDES STYLE META AI ─── */}
          <div className="w-full max-w-2xl mb-5" data-testid="quick-suggestions-mobile">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { icon: "✦", text: "Valider mon idée de projet", prompt: "Je veux valider mon idée de projet. Peux-tu m'analyser ça ?" },
                { icon: '💰', text: 'Analyser ma trésorerie', prompt: "Analyse ma situation financière et donne-moi des recommandations concrètes." },
                { icon: '🤖', text: 'Créer un agent IA', prompt: "Je veux créer un agent IA pour répondre à mes clients automatiquement." },
                { icon: '✍️', text: 'Rédiger un devis client', prompt: "Aide-moi à rédiger un devis professionnel pour un client." },
              ].map((s, i) => (
                <button key={i}
                  onClick={() => { setMessage(s.prompt); setTimeout(() => inputRef?.current?.focus(), 100); }}
                  style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '16px 20px', background: 'white', border: '1.5px solid #E5E7EB', borderRadius: '14px', cursor: 'pointer', textAlign: 'left', width: '100%', transition: 'all .15s', minHeight: '56px' }}
                  onMouseOver={e => { e.currentTarget.style.borderColor = '#1D4E8A'; e.currentTarget.style.background = '#F8F9FF'; }}
                  onMouseOut={e => { e.currentTarget.style.borderColor = '#E5E7EB'; e.currentTarget.style.background = 'white'; }}
                >
                  <span style={{ fontSize: '20px', flexShrink: 0 }}>{s.icon}</span>
                  <span style={{ fontSize: '16px', fontWeight: 500, color: '#1F2937' }}>{s.text}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Category tabs - horizontal scrollable */}
          <div className="w-full max-w-2xl mb-4" data-testid="quick-prompt-categories">
            <div className="flex overflow-x-auto gap-1.5 sm:gap-2 pb-1 md:justify-center" style={{scrollbarWidth:'none', WebkitOverflowScrolling:'touch'}}>
              {quickPromptCats.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setQuickCat(cat.id)}
                  className={`px-4 py-3 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                    quickCat === cat.id
                      ? 'bg-[#1D4E8A] text-white shadow-md'
                      : 'bg-[#F5F5F0] text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400'
                  }`}
                  data-testid={`quick-cat-${cat.id}`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Prompt cards - 2x2 grid */}
          {currentQuickCat && (
            <div className="w-full max-w-2xl mb-4 grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fadeIn" data-testid="quick-prompt-cards">
              {currentQuickCat.prompts.map((p, idx) => {
                const Icon = p.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => {
                      if (!localStorage.getItem('zayado_sync_choice') {
                        localStorage.setItem('zayado_sync_choice', 'internal');
                      }
                      setMode('quick');
                      setImageMode(false);
                      setAgentActive(false);
                      pendingAutoSendRef.current = p.prompt;
                      setMessage(p.prompt);
                    }}
                    className="flex items-start gap-2 sm:gap-3 p-2.5 sm:p-4 rounded-xl border border-[#E5E5E5] dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-[#1D4E8A]/40 hover:shadow-md transition-all text-left group"
                    data-testid={`quick-prompt-${quickCat}-${idx}`}
                  >
                    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl ${p.color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}>
                      <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs sm:text-sm font-semibold text-gray-900 dark:text-gray-100 line-clamp-1">{p.title}</div>
                      <div className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">{p.subtitle}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Prompt cards end - no more duplicates */}

        </div>

        {/* Fixed bottom section: Input bar + Sync */}
        <div className="shrink-0 px-3 sm:px-4 pb-3 sm:pb-4 bg-white dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 pt-2 sm:pt-3">
          {/* Attached files preview */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-1.5 px-3 py-2 mb-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-[#F5F5F0] dark:bg-gray-800">
              {attachedFiles.map((f, idx) => {
                const ext = (f.name || '').split('.').pop().toLowerCase();
                const fileIcons = { pdf: '📄', zip: '📦', docx: '📝', doc: '📝', xlsx: '📊', xls: '📊', png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', webp: '🖼️', txt: '📃', csv: '📊', mp4: '🎬', mp3: '🎵', md: '📋', json: '⚙️', html: '🌐', htm: '🌐', pptx: '📊', ppt: '📊' };
                const fileIcon = fileIcons[ext] || '📎';
                const sizeKb = f.size ? Math.round(f.size / 1024) : null;
                const hasExtract = f.extracted_text && f.extracted_text.length > 10;
                return (
                  <div key={idx} className="group flex items-center gap-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-2.5 py-1.5 text-[12px] text-gray-700 dark:text-gray-300 shadow-sm hover:border-[#1D4E8A]/40 transition-all">
                    <span className="text-[15px] leading-none">{fileIcon}</span>
                    <div className="flex flex-col min-w-0">
                      <span className="truncate max-w-[130px] font-medium">{f.name}</span>
                      {sizeKb && <span className="text-[10px] text-gray-400">{sizeKb > 1024 ? `${(sizeKb/1024).toFixed(1)} Mo` : `${sizeKb} Ko`}{hasExtract ? ' · Analyse' : ''}</span>}
                    </div>
                    <button onClick={() => removeFile(idx)} className="ml-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all p-0.5 rounded">
                      <svg viewBox="0 0 16 16" className="w-3 h-3 fill-current"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          <div className="max-w-2xl mx-auto">
            <div className="relative bg-white dark:bg-gray-800 border-[1.5px] border-[#E2DDD5] dark:border-gray-700 rounded-[14px] shadow-[0_1px_4px_rgba(0,0,0,0.04)] focus-within:border-[#1D4E8A] focus-within:shadow-[0_0_0_3px_rgba(29,78,138,0.08)] transition-all">
              {/* Toolbar INSIDE the input — Fichier, Image, Web, Dicter, Agent */}
              <div className="flex items-center gap-0.5 px-2 sm:px-3 pt-2 pb-0 border-b border-[#F5F3EF] overflow-x-auto" data-testid="input-toolbar-empty">
                <button onClick={() => fileInputRef.current?.click()} disabled={uploadingFile}
                  className="flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800 transition-colors shrink-0"
                  data-testid="chatbar-fichier-btn-empty" title="Joindre un fichier">
                  <Paperclip className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Fichier</span>
                </button>
                <button onClick={() => { if (imageMode) { setImageMode(false); } else { setImageMode(true); } inputRef.current?.focus(); }}
                  className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${imageMode ? 'bg-[#0F1E3C] text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                  data-testid="chatbar-image-btn-empty" title="Generer une image">
                  <Image className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Image</span>
                </button>
                <button onClick={() => { if (mode === 'perplexity') handleModeChange('fast'); else handleModeChange('perplexity'); inputRef.current?.focus(); }}
                  className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${mode === 'perplexity' && !imageMode ? 'bg-[#0F1E3C] text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                  data-testid="chatbar-web-btn-empty" title="Recherche web">
                  <Globe className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Web</span>
                </button>
                <div className="w-px h-4 bg-[#E2DDD5] mx-0.5 sm:mx-1 shrink-0" />
                <button onClick={toggleRecording}
                  className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${isRecording ? 'bg-red-500 text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                  data-testid="chatbar-dicter-btn-empty" title={isRecording ? 'Arreter' : 'Dicter'}>
                  {isRecording ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />} <span className="hidden sm:inline">Dicter</span>
                </button>
                <div className="ml-auto shrink-0">
                  <button ref={agentToggleRef} onClick={toggleAgentPicker}
                    className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs font-medium transition-colors ${selectedAgent || agentActive ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-[#1D4E8A]'}`}
                    data-testid="agent-toggle-btn-empty" title={selectedAgent ? selectedAgent.name : 'Agent autonome'}>
                    <Bot className="w-3.5 h-3.5" /> <span className="hidden sm:inline">{selectedAgent ? selectedAgent.name : 'Agent autonome'}</span><span className="sm:hidden">{selectedAgent ? selectedAgent.name.slice(0, 5) : 'Agent'}</span>
                  </button>
                </div>
              </div>
              {/* Agent Picker Dropdown rendered via portal */}
              {/* Textarea */}
              <div className="flex items-center">
                <input ref={fileInputRef} type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.zip,.md,.json" className="hidden" onChange={handleFileUpload} data-testid="file-input-empty" />
                <textarea
                  ref={inputRef}
                  value={message}
                  onChange={e => {
                    const val = e.target.value;
                    setMessage(val);
                    // Afficher le menu slash dès que l'utilisateur tape "/" en début de message
                    if (val.startsWith('/')) {
                      setShowSlashMenu(true);
                      setSlashActiveIdx(0);
                    } else {
                      setShowSlashMenu(false);
                    }
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder={imageMode ? "Décrivez l'image souhaitée..." : 'Posez votre question ou tapez / pour les commandes...'}
                  rows={1}
                  style={{ minHeight: '52px', maxHeight: '180px' }}
                  className="flex-1 bg-transparent px-3.5 py-2.5 text-gray-900 dark:text-gray-100 placeholder-gray-400 resize-none focus:outline-none text-sm"
                  data-testid="chat-input"
                />
                {/* Slash command menu (nouveau) */}
                {showSlashMenu && (
                  <SlashCommandMenu
                    query={message}
                    activeIndex={slashActiveIdx}
                    setActiveIndex={setSlashActiveIdx}
                    onSelect={(cmd) => { setMessage(cmd); setShowSlashMenu(false); setSlashActiveIdx(0); inputRef.current?.focus(); }}
                    onClose={() => { setShowSlashMenu(false); setSlashActiveIdx(0); }}
                  />
                )}
              </div>
              {/* Bottom: hint chips + send/stop */}
              <div className="flex items-center justify-between px-3 pb-2 pt-0.5">
                {!isStreaming ? (
                  <div className="flex gap-1.5">
                    {['Diagnostic', 'Organiser', 'Analyser'].map(h => (
                      <button key={h} onClick={() => { setMessage(h); inputRef.current?.focus(); }}
                        className="px-2 py-0.5 rounded-full border border-[#E2DDD5] text-[11px] text-gray-400 hover:border-[#1D4E8A] hover:text-[#0F1E3C] transition-colors"
                        data-testid={`hint-chip-${h.toLowerCase()}`}>
                        {h}
                      </button>
                    ))}
                  </div>
                ) : <div />}
                {isStreaming ? (
                  <button onClick={handleAbort}
                    className="w-[34px] h-[34px] bg-red-500 hover:bg-red-600 rounded-[9px] flex items-center justify-center transition-colors animate-pulse"
                    data-testid="chat-stop-btn-empty">
                    <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!message.trim() && attachedFiles.length === 0}
                    className="w-[34px] h-[34px] bg-[#0F1E3C] hover:bg-[#152F5C] disabled:opacity-30 rounded-[9px] flex items-center justify-center transition-colors"
                    data-testid="chat-send"
                  >
                    <Send className="w-4 h-4 text-white" />
                  </button>
                )}
              </div>
            </div>
            {/* Bottom action row — masquée sur mobile */}
            <div className="hidden sm:flex items-center justify-between mt-2 px-1">
              <div className="flex items-center gap-1.5">
                <button onClick={handleSyncDrive} disabled={syncingDrive || autoSyncing}
                  className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors disabled:opacity-60 ${
                    (syncingDrive || autoSyncing) ? 'bg-blue-500 text-white border-blue-500' :
                    (driveConnected.google || driveConnected.onedrive) ? 'bg-[#1D4E8A] text-white border-[#1D4E8A]' :
                    'bg-white border-[#E2DDD5] text-gray-500 hover:bg-gray-100'
                  }`}
                  data-testid="sync-drive-empty-btn">
                  {(syncingDrive || autoSyncing) ? <Loader2 className="w-3 h-3 animate-spin" /> :
                   (driveConnected.google || driveConnected.onedrive) ? <Cloud className="w-3 h-3" /> :
                   <CloudOff className="w-3 h-3" />}
                  {(syncingDrive || autoSyncing) ? 'Sync...' : (driveConnected.google || driveConnected.onedrive) ? 'Sync' : 'Cloud'}
                </button>
                {lastSyncTime && (
                  <span className="text-[9px] text-gray-400 hidden sm:inline" data-testid="last-sync-time-empty">{lastSyncTime}</span>
                )}
              </div>
              <div className="flex items-center gap-1.5">
                <div className="relative" data-testid="prompts-dropdown-wrapper-empty">
                  <button onClick={() => setShowPromptsDropdown(prev => !prev)}
                    className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors ${showPromptsDropdown ? 'bg-[#0F1E3C] text-white border-[#0F1E3C]' : 'border-[#E2DDD5] text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                    data-testid="chatbar-prompts-btn-empty" title="Prompts rapides">
                    <Sparkles className="w-3 h-3" /> Prompts <ChevronDown className={`w-2.5 h-2.5 transition-transform ${showPromptsDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  {showPromptsDropdown && (
                    <div className="absolute bottom-full right-0 mb-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-40 max-h-96 overflow-y-auto animate-fadeIn" data-testid="prompts-dropdown-list-empty">
                      {/* Header + bouton ajout */}
                      <div className="p-3 border-b border-gray-100 flex items-center justify-between">
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Prompts rapides</p>
                        <button onClick={() => setShowAddPrompt(prev => !prev)}
                          className="text-[10px] flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1E3A8A]/10 text-[#1E3A8A] hover:bg-[#1E3A8A]/20 transition-colors font-medium">
                          <Plus className="w-3 h-3" /> Nouveau
                        </button>
                      </div>
                      {/* Formulaire ajout */}
                      {showAddPrompt && (
                        <div className="p-3 border-b border-gray-100 bg-[#F8F9FF] space-y-2">
                          <input value={newPromptTitle} onChange={e => setNewPromptTitle(e.target.value)}
                            placeholder="Titre du prompt..." className="w-full text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-[#1E3A8A]" />
                          <textarea value={newPromptText} onChange={e => setNewPromptText(e.target.value)}
                            placeholder="Contenu du prompt..." rows={3}
                            className="w-full text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-[#1E3A8A] resize-none" />
                          <div className="flex items-center gap-2">
                            <select value={newPromptAction} onChange={e => setNewPromptAction(e.target.value)}
                              className="text-xs border border-gray-200 rounded-lg px-2 py-1 outline-none flex-1">
                              <option value="insert">Insert (coller)</option>
                              <option value="auto_send">Auto (envoyer)</option>
                            </select>
                            <button onClick={saveNewPrompt} disabled={savingPrompt || !newPromptTitle.trim() || !newPromptText.trim()}
                              className="text-xs px-3 py-1 bg-[#1E3A8A] text-white rounded-lg hover:bg-[#152F5C] disabled:opacity-40 transition-colors">
                              {savingPrompt ? '...' : 'Sauver'}
                            </button>
                          </div>
                        </div>
                      )}
                      {/* Section Prompts Extension IA (system) */}
                      {systemPrompts.length > 0 && (
                        <div>
                          <div className="px-3 pt-2.5 pb-1 flex items-center gap-1.5">
                            <span className="text-[9px] font-bold text-[#1E3A8A] uppercase tracking-wider bg-[#EEF2FF] px-1.5 py-0.5 rounded">Extension IA by Zayado</span>
                          </div>
                          <div className="px-1.5 pb-1">
                            {systemPrompts.map(p => (
                              <button key={p.id || p.title} onClick={() => { window.dispatchEvent(new CustomEvent('insertPrompt', { detail: { prompt: p.prompt, action: p.action } })); setShowPromptsDropdown(false); }}
                                className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-[#EEF2FF] text-left transition-colors">
                                <div className="flex-1 min-w-0"><span className="text-sm font-medium text-gray-800 truncate block">{p.title}</span><p className="text-[10px] text-gray-400 truncate mt-0.5">{p.prompt}</p></div>
                                <span className="text-[9px] px-1.5 py-0.5 rounded shrink-0 ml-2 bg-[#EEF2FF] text-[#1E3A8A] font-semibold">{p.action === 'auto_send' ? '⚡ Auto' : '⚡ Insert'}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Section Mes Prompts (user) */}
                      {userPrompts.length > 0 && (
                        <div>
                          <div className="px-3 pt-2.5 pb-1 flex items-center gap-1.5">
                            <span className="text-[9px] font-bold text-gray-500 uppercase tracking-wider bg-gray-100 px-1.5 py-0.5 rounded">✏️ Mes prompts</span>
                          </div>
                          <div className="px-1.5 pb-1">
                            {userPrompts.map(p => (
                              <button key={p.id || p.title} onClick={() => { window.dispatchEvent(new CustomEvent('insertPrompt', { detail: { prompt: p.prompt, action: p.action } })); setShowPromptsDropdown(false); }}
                                className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-[#F5F3EF] text-left transition-colors">
                                <div className="flex-1 min-w-0"><span className="text-sm font-medium text-gray-800 truncate block">{p.title}</span><p className="text-[10px] text-gray-400 truncate mt-0.5">{p.prompt}</p></div>
                                <span className={`text-[9px] px-1.5 py-0.5 rounded shrink-0 ml-2 ${p.action === 'auto_send' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'}`}>{p.action === 'auto_send' ? 'Auto' : 'Insert'}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {systemPrompts.length === 0 && userPrompts.length === 0 && (
                        <div className="p-4 text-center">
                          <p className="text-xs text-gray-400">Aucun prompt configuré.</p>
                          <p className="text-[10px] text-gray-300 mt-1">Cliquez sur "+ Nouveau" pour en créer un.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {supportHumain.has && (
                  <button onClick={toggleSupportHumain}
                    className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors ${
                      supportHumain.active ? 'bg-green-50 border-green-300 text-green-700' : 'border-[#E2DDD5] text-gray-500 hover:text-green-600'
                    }`} data-testid="support-humain-toggle-empty">
                    <Headphones className="w-3 h-3" /> {supportHumain.active ? 'Support actif' : 'Support'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* BYOK API Key Modal (empty state) */}
        {showByokModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowByokModal(false)} data-testid="byok-modal-overlay">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[440px] mx-4 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="byok-modal">
              <div className="p-6 text-center">
                <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-[#1D4E8A]/10 flex items-center justify-center">
                  <Key className="w-7 h-7 text-[#1D4E8A]" />
                </div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">Cle API OpenAI requise</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
                  Pour utiliser le mode ChatGPT BYOK, vous devez d abord configurer votre cle API OpenAI dans vos parametres.
                </p>
                <div className="bg-[#F5F5F0] dark:bg-gray-700 rounded-xl p-4 text-left mb-4 space-y-2">
                  <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-bold text-[#1D4E8A] shrink-0">1.</span>
                    <span>Obtenez votre cle sur <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-[#1D4E8A] underline hover:text-[#1D4E8A]/80">platform.openai.com</a></span>
                  </div>
                  <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-bold text-[#1D4E8A] shrink-0">2.</span>
                    <span>Cliquez sur "Ouvrir Paramètres" ci-dessous</span>
                  </div>
                  <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-bold text-[#1D4E8A] shrink-0">3.</span>
                    <span>Collez votre cle (commence par <code className="bg-gray-200 dark:bg-gray-600 px-1 rounded text-xs">sk-...</code>)</span>
                  </div>
                </div>
                <button onClick={() => {
                  const demoUrl = safeLocalGet('zayado_demo_url')} className="inline-flex items-center gap-1.5 text-xs text-[#1D4E8A] hover:underline mb-4" data-testid="byok-tutorial-link">
                  <Info className="w-3.5 h-3.5" /> Voir le tutoriel video
                </button>
                <div className="flex gap-3">
                  <button onClick={() => setShowByokModal(false)} className="flex-1 px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-xl transition-colors" data-testid="byok-modal-cancel">
                    Annuler
                  </button>
                  <button onClick={() => { setShowByokModal(false); window.dispatchEvent(new CustomEvent('openSettingsTab', { detail: { tab: 'api' } })); }}
                    className="flex-1 px-4 py-2.5 bg-[#1D4E8A] text-white text-sm font-medium rounded-xl hover:bg-[#1D4E8A]/90 transition-colors flex items-center justify-center gap-2" data-testid="byok-modal-settings">
                    <Settings className="w-4 h-4" /> Ouvrir Paramètres
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Agent IA Confirmation Modal (empty state) */}
        {showAgentConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => { setShowAgentConfirm(false); setPendingAgentMessage(null); }} data-testid="agent-confirm-overlay">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[460px] mx-4 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="agent-confirm-modal">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Confirmer la tache Agent IA</h2>
                    <p className="text-xs text-gray-500">Verification avant execution</p>
                  </div>
                </div>
                <div className="bg-[#F5F5F0] dark:bg-gray-700 rounded-xl p-4 mb-4 space-y-3">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    <div className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Vos credits</div>
                    <div className="flex items-center justify-between py-1.5 border-b border-gray-200/60 dark:border-gray-600">
                      <span>Credits disponibles</span>
                      <span className="font-bold text-[#1D4E8A]">{user?.credits || 0}</span>
                    </div>
                    <div className="flex items-center justify-between py-1.5 border-b border-gray-200/60 dark:border-gray-600">
                      <span>Chat IA (Claude, Gemini...)</span>
                      <span className="text-gray-500">2-4 credits/msg</span>
                    </div>
                    <div className="flex items-center justify-between py-1.5">
                      <span>Agent IA (taches autonomes)</span>
                      <span className="font-semibold text-amber-600">60-600 credits</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl mb-4">
                  <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                  <p className="text-xs text-amber-700 dark:text-amber-300">Les taches Agent IA consomment plus de credits car elles s executent de maniere autonome et peuvent prendre plusieurs minutes.</p>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => { setShowAgentConfirm(false); setPendingAgentMessage(null); }} className="flex-1 px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-xl transition-colors" data-testid="agent-confirm-cancel">
                    Annuler
                  </button>
                  <button onClick={() => { setShowAgentConfirm(false); handleSend(); }} className="flex-1 px-4 py-2.5 bg-[#1D4E8A] text-white text-sm font-medium rounded-xl hover:bg-[#1D4E8A]/90 transition-colors" data-testid="agent-confirm-proceed">
                    Continuer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Sync Choice Prompt — first-time chat (empty state) */}
        {/* Sync prompt removed — auto-sync is now controlled via Settings → General → Synchronisation */}

        {/* Agent Picker Portal — for empty state */}
        {showAgentPicker && createPortal(
          <div
            className="fixed w-56 max-h-72 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-1.5 animate-fadeIn"
            style={{ top: Math.max(8, agentPickerPos.top - 300), left: agentPickerPos.left, zIndex: 9999 }}
            data-testid="agent-picker-dropdown"
          >
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-2 mb-1">Choisir un agent</p>
            <button onClick={() => { setSelectedAgent(null); setShowAgentPicker(false); }}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors ${!selectedAgent ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200'}`}
              data-testid="agent-pick-default">
              <Sparkles className="w-4 h-4" />
              <div>
                <span className="text-sm font-semibold">Extension IA by Zayado</span>
                <p className="text-[10px] text-gray-400">Assistant par defaut</p>
              </div>
            </button>
            {customAgents.map(agent => (
              <button key={agent.id} onClick={() => selectAgent(agent)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors ${selectedAgent?.id === agent.id ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200'}`}
                data-testid={`agent-pick-${agent.id}`}>
                <div className="w-4 h-4 rounded-full shrink-0" style={{ background: agent.color || '#1D4E8A' }} />
                <div className="min-w-0">
                  <span className="text-sm font-semibold truncate block">{agent.name}</span>
                  <p className="text-[10px] text-gray-400 truncate">{agent.system_prompt?.slice(0, 40) || 'Agent personnalise'}</p>
                </div>
              </button>
            ))}
            {customAgents.length === 0 && (
              <p className="text-xs text-gray-400 text-center py-2">Aucun agent. Creez-en dans Parametres.</p>
            )}
          </div>,
          document.body
        )}
      </div>
    );
  }

  // Chat with messages
  return (
    <div className="flex flex-col h-full overflow-hidden" data-testid="chat-interface">
      {/* Mode bar — 5 main modes + extra toggle + image mode indicator */}
      <div className="border-b border-[#E5E5E5] dark:border-gray-700 px-4 py-2 flex items-center justify-between bg-white dark:bg-gray-900 shrink-0 overflow-x-auto" data-testid="mode-bar">
        <div className="flex items-center gap-1 shrink-0">
          {imageMode ? (
            /* Image Mode Active — show blue pastel bar */
            <div className="flex items-center gap-2" data-testid="image-mode-bar">
              <div className="flex items-center gap-2 bg-[#E8F4F8] dark:from-blue-900/20 border border-[#1D4E8A]/20 dark:border-blue-700 rounded-lg px-3 py-1.5">
                <Image className="w-4 h-4 text-[#1D4E8A]" />
                <span className="text-xs font-bold text-[#1D4E8A] dark:text-blue-300">Mode Image IA</span>
                <span className="text-[10px] text-[#1D4E8A]/60 dark:text-blue-400">8 credits/image</span>
              </div>
              {/* Image model selector */}
              <div className="flex items-center gap-0.5 bg-white/60 dark:bg-gray-800 rounded-lg p-0.5">
                {imageModels(lang).map(im => (
                  <button
                    key={im.id}
                    onClick={() => setImageModel(im.id)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                      imageModel === im.id ? 'bg-white dark:bg-gray-700 shadow-sm text-[#1D4E8A] dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                    data-testid={`image-model-${im.id}`}
                  >
                    <span>{im.label}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${imageModel === im.id ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'bg-gray-200 text-gray-500'}`}>{im.badge}</span>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setImageMode(false)}
                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-gray-600"
                data-testid="exit-image-mode"
                title="Quitter le mode Image"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            /* Normal text mode tabs */
            <>
              {/* === MOBILE : dropdown compact style ChatGPT === */}
              <div className="relative sm:hidden" data-testid="mobile-mode-dropdown">
                <button
                  onClick={() => setShowExtraModes(!showExtraModes)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 bg-white text-xs font-semibold text-gray-800 shadow-sm"
                  data-testid="mobile-mode-btn"
                >
                  {React.createElement(currentMode.icon, { className: 'w-3.5 h-3.5 text-[#1D4E8A]' })}
                  <span>{currentMode.label}</span>
                  <ChevronDown className="w-3 h-3 text-gray-400" />
                </button>
                {showExtraModes && (
                  <div className="fixed inset-0 z-[200]" onClick={() => setShowExtraModes(false)}>
                    <div className="fixed left-4 right-4 bottom-[45vh] bg-white border border-gray-200 rounded-xl shadow-2xl z-[201] py-1 max-h-[50vh] overflow-y-auto" data-testid="mobile-mode-menu" onClick={e => e.stopPropagation()}>
                    {modes.map(m => {
                      const Icon = m.icon;
                      return (
                        <button key={m.id}
                          onClick={() => { handleModeChange(m.id); setShowExtraModes(false); }}
                          className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors ${
                            mode === m.id ? 'bg-[#1D4E8A]/8 text-[#1D4E8A] font-semibold' : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          data-testid={`mobile-mode-item-${m.id}`}
                        >
                          <Icon className={`w-4 h-4 ${mode === m.id ? 'text-[#1D4E8A]' : 'text-gray-400'}`} />
                          <div className="flex-1 text-left">
                            <div className="font-medium">{m.label}</div>
                            <div className="text-[10px] text-gray-400">{m.desc}</div>
                          </div>
                          {mode === m.id && <Check className="w-3.5 h-3.5 text-[#1D4E8A]" />}
                        </button>
                      );
                    })}
                    <div className="border-t border-gray-100 mt-1 pt-1">
                      <button
                        onClick={() => { setImageMode(true); setImageModel('nano-banana'); setShowExtraModes(false); }}
                        className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                        data-testid="mobile-mode-item-image"
                      >
                        <Image className="w-4 h-4 text-gray-400" />
                        <div className="flex-1 text-left">
                          <div className="font-medium">Image IA</div>
                          <div className="text-[10px] text-gray-400">Génération d'images · 8 crédits</div>
                        </div>
                      </button>
                    </div>
                  </div>
                  </div>
                )}
              </div>
              {/* === DESKTOP : tabs normaux === */}
              <div className="hidden sm:flex items-center gap-0.5 bg-white/60 dark:bg-gray-800 rounded-lg p-0.5">
                {modes.map((m, idx) => {
                  const Icon = m.icon;
                  return (
                    <React.Fragment key={m.id}>
                      <button
                        onClick={() => handleModeChange(m.id)}
                        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                          m.isAgent
                            ? (mode === m.id ? 'bg-orange-600 text-white shadow-sm' : 'text-orange-600 hover:bg-orange-50 border border-orange-200')
                            : (mode === m.id ? 'bg-[#1D4E8A] text-white shadow-sm' : 'text-[#1D4E8A]/70 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5 dark:hover:text-blue-300')
                        }`}
                        data-testid={`mode-tab-${m.id}`}
                        title={`${m.label} — ${m.desc}`}
                      >
                        <Icon className={`w-3.5 h-3.5 ${mode === m.id ? 'text-white' : m.isAgent ? 'text-orange-500' : 'text-[#1D4E8A]/60'}`} />
                        <span>{m.label}</span>
                        {m.isAgent && <span className="text-[9px] px-1 py-0.5 rounded bg-orange-100 text-orange-600 ml-0.5 font-bold">AUTO</span>}
                      </button>
                      {m.separator_after && <div className="w-px h-5 bg-gray-200 dark:bg-gray-600 mx-0.5 flex-shrink-0" />}
                    </React.Fragment>
                  );
                })}
              </div>
              {/* Image mode button — desktop seulement */}
              <div className="hidden sm:block w-px h-5 bg-gray-200 dark:bg-gray-600 mx-0.5 flex-shrink-0" />
              <button onClick={() => { setImageMode(!imageMode); if (!imageMode) setImageModel('nano-banana'); }}
                className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${imageMode ? 'bg-[#1D4E8A] text-white shadow-sm' : 'text-[#1D4E8A]/70 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5'}`}
                data-testid="toggle-image-mode" title="Mode Image IA">
                <Image className={`w-3.5 h-3.5 ${imageMode ? 'text-white' : 'text-[#1D4E8A]/60'}`} />
                <span>Image</span>
              </button>
            </>
          )}
        </div>
        {/* Right: Nouveau + Screenshot + Zoom + Info (i) button */}
        <div className="flex items-center gap-1">
          <button onClick={() => { navigate('/app'); window.location.reload(); }}
            className="p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 text-[#1D4E8A]/60 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5"
            data-testid="new-conv-btn-conv" title="Nouvelle conversation">
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[10px]">Nouveau</span>
          </button>
          <button onClick={handleScreenCapture}
            className="p-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 text-[#1D4E8A]/60 hover:text-[#1D4E8A] hover:bg-[#1D4E8A]/5"
            data-testid="screenshot-btn-conv" title="Capturer l'ecran">
            <Camera className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[10px]">Screenshot</span>
          </button>
          <div className="w-px h-4 bg-gray-200 mx-0.5" />
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg px-1.5 py-1">
            <button onClick={() => { const v = Math.max(70, chatZoom - 10); setChatZoom(v); localStorage.setItem('zayado_chat_zoom', v); }} className="w-5 h-5 rounded text-gray-500 hover:text-gray-800 text-xs font-bold flex items-center justify-center hover:bg-gray-200" data-testid="zoom-minus">-</button>
            <span className="text-[10px] font-medium text-gray-500 w-6 text-center">{chatZoom}%</span>
            <button onClick={() => { const v = Math.min(150, chatZoom + 10); setChatZoom(v); localStorage.setItem('zayado_chat_zoom', v); }} className="w-5 h-5 rounded text-gray-500 hover:text-gray-800 text-xs font-bold flex items-center justify-center hover:bg-gray-200" data-testid="zoom-plus">+</button>
          </div>
          <button onClick={() => setShowChatInfo(!showChatInfo)} className="w-6 h-6 rounded-full border-2 border-[#1D4E8A]/30 text-[#1D4E8A] hover:border-[#1D4E8A] hover:bg-[#1D4E8A]/5 flex items-center justify-center text-xs font-bold transition-colors relative" data-testid="chat-info-btn-modebar" title="Info conversation">
            i
          </button>
        </div>
      </div>

      {/* Chat Info Popover — 2 columns with credits + actions */}
      {showChatInfo && (
        <div ref={chatInfoRef} className="absolute right-4 top-12 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden" data-testid="chat-info-popover">
          <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <span className="text-xs font-bold text-gray-900 dark:text-gray-100">{lang === 'en' ? 'Conversation info' : 'Info conversation'}</span>
            <button onClick={() => setShowChatInfo(false)} className="text-gray-400 hover:text-gray-600"><X className="w-3.5 h-3.5" /></button>
          </div>
          {conversationCreatedAt && (
            <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700">
              <div className="text-[10px] text-gray-400">{lang === 'en' ? 'Created on' : 'Créé le'}</div>
              <div className="text-xs font-medium text-gray-700 dark:text-gray-300" data-testid="chat-info-created-at">
                {new Date(conversationCreatedAt).toLocaleDateString(lang === 'en' ? 'en-US' : 'fr-FR', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-0">
            <div className="px-4 py-2.5 border-b border-r border-gray-100 dark:border-gray-700">
              <div className="text-[10px] text-gray-400">{lang === 'en' ? 'Total credits spent' : 'Total crédits dépensés'}</div>
              <div className="text-sm font-bold text-[#C7372F]" data-testid="chat-info-credits">{totalCreditsUsed || creditsUsed} credits</div>
            </div>
            <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-700">
              <div className="text-[10px] text-gray-400">Messages</div>
              <div className="text-sm font-bold text-[#1D4E8A]" data-testid="chat-info-messages">{messages.length}</div>
            </div>
          </div>
          <div className="p-2 flex gap-1">
            <button onClick={() => {
              navigator.clipboard.writeText(window.location.href);
              toast.success('Lien copie !');
              setShowChatInfo(false);
            }}
              className="flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-testid="chat-info-share">
              <ExternalLink className="w-3.5 h-3.5" /> Partager
            </button>
            <button onClick={async () => {
              try {
                const res = await fetch(`${API}/api/conversations/${conversationId}/export/pdf`, { headers: { Authorization: `Bearer ${token}` } });
                if (res.ok) { const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'conversation.pdf'; a.click(); }
              } catch {} setShowChatInfo(false);
            }} className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-testid="chat-info-download-pdf">
              <FileDown className="w-3.5 h-3.5" /> PDF
            </button>
            <button onClick={async () => {
              try {
                const res = await fetch(`${API}/api/conversations/${conversationId}/export/docx`, { headers: { Authorization: `Bearer ${token}` } });
                if (res.ok) { const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'conversation.docx'; a.click(); }
              } catch {} setShowChatInfo(false);
            }} className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-testid="chat-info-download-docx">
              <FileDown className="w-3.5 h-3.5" /> Word
            </button>
            <button onClick={async () => {
              try {
                const res = await fetch(`${API}/api/conversations/${conversationId}/export/pptx`, { headers: { Authorization: `Bearer ${token}` } });
                if (res.ok) { const blob = await res.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'conversation.pptx'; a.click(); }
              } catch {} setShowChatInfo(false);
            }} className="flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-testid="chat-info-download-pptx">
              <FileDown className="w-3.5 h-3.5" /> PPT
            </button>
          </div>
        </div>
      )}

      {/* Drive Nudge Banner — max 2 times */}
      {showDriveNudge && (
        <div className="mx-4 mt-3 flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl px-4 py-3" data-testid="drive-nudge-banner">
          <div className="w-7 h-7 bg-[#1D4E8A] rounded-lg flex items-center justify-center shrink-0">
            <Upload className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[#1D4E8A]">Sauvegardez vos résultats dans le cloud</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Connectez Google Drive ou OneDrive pour sauvegarder automatiquement vos rapports et images. 
              <span className="text-gray-400 italic ml-1">Sinon, vos données sont stockées sur nos serveurs pendant 12 mois et peuvent être supprimées sur demande.</span>
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button onClick={() => {
              window.dispatchEvent(new CustomEvent('openSettingsTab', { detail: { tab: 'drive' } }));
            }} className="text-xs bg-[#1D4E8A] text-white px-3 py-1.5 rounded-lg hover:bg-[#1D4E8A]/90 transition-colors font-medium" data-testid="drive-nudge-connect-btn">Connecter</button>
            <button onClick={() => {
              try { localStorage.setItem('zayado_drive_nudge', String((parseInt(safeLocalGet('zayado_drive_nudge') catch {}
              setShowDriveNudge(false);
            }} className="p-1 text-gray-400 hover:text-gray-600 rounded-md">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Messages — scrollable area WHITE background */}
      <div ref={scrollContainerRef} style={{ height: 0, flexGrow: 1, overflowY: 'auto', zoom: chatZoom / 100 }} className="px-4 py-6 bg-white dark:bg-gray-900 relative" data-testid="chat-messages-scroll"
        onScroll={handleScroll}>
        <div className="max-w-4xl mx-auto space-y-8">
          {messages.map((msg, i) => {
            // Detect mode changes for AI model indicator
            const prevUserMsg = messages.slice(0, i).reverse().find(m => m.role === 'user');
            const currentUserMsg = msg.role === 'user' ? msg : null;
            const msgMode = currentUserMsg?.mode || prevUserMsg?.mode || mode;
            const modeInfo = [...modes, ...extras].find(m => m.id === msgMode);
            
            // Show model indicator: on first assistant message, or when mode changes
            let showModelIndicator = false;
            if (msg.role === 'assistant' && i > 0) {
              const thisUserMsg = messages.slice(0, i).reverse().find(m => m.role === 'user');
              const prevAssistantIdx = messages.slice(0, i).findLastIndex(m => m.role === 'assistant');
              if (prevAssistantIdx === -1) {
                showModelIndicator = true; // First assistant response
              } else {
                const prevAssistUserMsg = messages.slice(0, prevAssistantIdx).reverse().find(m => m.role === 'user');
                if (thisUserMsg?.mode && prevAssistUserMsg?.mode && thisUserMsg.mode !== prevAssistUserMsg.mode) {
                  showModelIndicator = true; // Mode changed
                }
              }
            }
            
            return (
            <React.Fragment key={i}>
              {showModelIndicator && modeInfo && (
                <div className="flex items-center gap-2 justify-center py-2 my-1" data-testid={`model-indicator-${i}`}>
                  <div className="h-[1.5px] flex-1 bg-[#1D4E8A]/20 dark:bg-gray-600" />
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-[#EEF2FF] dark:bg-gray-800 border border-[#1D4E8A]/20 rounded-full shadow-sm">
                    {React.createElement(modeInfo.icon, { className: 'w-3 h-3 text-[#1D4E8A]' })}
                    <span className="text-[10px] font-semibold text-[#1D4E8A] dark:text-blue-300">{modeInfo.label}</span>
                  </div>
                  <div className="h-[1.5px] flex-1 bg-[#1D4E8A]/20 dark:bg-gray-600" />
                </div>
              )}
            <div className={`flex gap-3 animate-fadeIn ${msg.role === 'user' ? 'justify-end' : 'items-start'}`} style={{ animationDelay: `${i * 30}ms` }}>
              {/* Bulle utilisateur : bleu d'origine. IA : texte libre sans bulle (style Claude) — pas de logo/avatar IA */}
              <div className={`max-w-[80%] ${
                msg.role === 'user'
                  ? 'bg-[#1D4E8A] text-white rounded-2xl rounded-br-none px-5 py-3.5 shadow-sm'
                  : 'px-1 py-0'
              }`}>
                {/* Image generation animation - stays visible while generating, even if partial content arrives */}
                {msg.role === 'assistant' && i === messages.length - 1 && isImageGenerating && !(msg.content && (msg.content.includes('data:image') || msg.content.includes('!['))) ? (
                    <div className="w-full max-w-[320px]" data-testid="image-generating-animation">
                      {/* Card style ChatGPT */}
                      <div className="relative rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg">
                        {/* Image placeholder avec shimmer */}
                        <div className="relative aspect-square bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 overflow-hidden">
                          {/* Shimmer sweep */}
                          <div className="absolute inset-0" style={{
                            background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.4) 50%, transparent 60%)',
                            animation: 'shimmerSweep 1.8s ease-in-out infinite',
                            backgroundSize: '200% 100%'
                          }} />
                          {/* Pulse center icon */}
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="relative">
                              <div className="w-16 h-16 rounded-2xl bg-white/80 dark:bg-gray-700/80 backdrop-blur-sm shadow-xl flex items-center justify-center">
                                <Image className="w-8 h-8 text-[#1D4E8A]" style={{ animation: 'iconBreath 2s ease-in-out infinite' }} />
                              </div>
                              <div className="absolute -inset-2 rounded-2xl border-2 border-[#1D4E8A]/20" style={{ animation: 'ripple 2s ease-out infinite' }} />
                            </div>
                          </div>
                          {/* Corner badge modèle */}
                          <div className="absolute top-3 left-3 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-2.5 py-1 flex items-center gap-1.5 shadow-sm">
                            <div className="w-1.5 h-1.5 rounded-full bg-amber-400" style={{ animation: 'thinkDot 1s ease-in-out infinite' }} />
                            <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200">Image IA</span>
                          </div>
                        </div>
                        {/* Footer infos */}
                        <div className="px-4 py-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-semibold text-gray-700 dark:text-gray-200">
                              {imageProgress < 25 ? '🎨 Initialisation...' : imageProgress < 55 ? '⚡ Génération en cours...' : imageProgress < 85 ? '🖌️ Finalisation...' : '✅ Presque prêt...'}
                            </span>
                            <span className="text-xs font-bold text-[#1D4E8A]">{Math.round(imageProgress)}%</span>
                          </div>
                          {/* Progress bar */}
                          <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-700 ease-out" style={{
                              width: `${Math.round(imageProgress)}%`,
                              background: 'linear-gradient(90deg, #1D4E8A, #2563EB, #C7372F)',
                              backgroundSize: '200% 100%',
                              animation: 'progressGlow 1.5s linear infinite'
                            }} />
                          </div>
                          <p className="text-[10px] text-gray-400 mt-1.5 text-center">Estimation : 15–30 secondes</p>
                        </div>
                      </div>
                      <style>{`
                        @keyframes shimmerSweep { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
                        @keyframes iconBreath { 0%,100%{transform:scale(1);opacity:0.8} 50%{transform:scale(1.1);opacity:1} }
                        @keyframes ripple { 0%{transform:scale(1);opacity:0.6} 100%{transform:scale(1.5);opacity:0} }
                        @keyframes progressGlow { 0%{background-position:0% 0%} 100%{background-position:200% 0%} }
                        @keyframes thinkDot { 0%,100%{transform:scale(0.6);opacity:0.4} 50%{transform:scale(1);opacity:1} }
                      `}</style>
                    </div>
                ) : null}
                {/* Thinking animation - shown while streaming with no content (non-image mode) */}
                {msg.role === 'assistant' && isStreaming && i === messages.length - 1 && !msg.content && !isImageGenerating && (
                    <div className="py-2" data-testid="thinking-animation">
                      {(() => {
                        const phrases = [
                          'Je reflechis',
                          'J analyse votre demande',
                          'Je recherche les informations',
                          'Je formule une reponse',
                          'Presque pret',
                        ];
                        return (
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500 dark:text-gray-400 italic" style={{ minWidth: '180px' }}>
                              {phrases[thinkingPhrase]}
                            </span>
                            <span className="flex items-center gap-0.5">
                              {[0, 1, 2].map(d => (
                                <span key={d} className="inline-block w-1.5 h-1.5 bg-[#1D4E8A] rounded-full"
                                  style={{ animation: 'thinkDot 1.2s ease-in-out infinite', animationDelay: `${d * 0.2}s` }} />
                              ))}
                            </span>
                            <style>{`
                              @keyframes thinkDot {
                                0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
                                40% { transform: scale(1); opacity: 1; }
                              }
                            `}</style>
                          </div>
                        );
                      })()}
                    </div>
                )}
                {msg.files && msg.files.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {msg.files.map((f, fi) => {
                      const ext = (f.name || '').split('.').pop().toLowerCase();
                      const icons = { pdf: '📄', zip: '📦', docx: '📝', doc: '📝', xlsx: '📊', xls: '📊', png: '🖼️', jpg: '🖼️', jpeg: '🖼️', txt: '📃', csv: '📊', mp4: '🎬', mp3: '🎵' };
                      const icon = icons[ext] || '📎';
                      const sizeKb = f.size ? Math.round(f.size / 1024) : null;
                      return f.url ? (
                          <a key={fi} href={`${API}${f.url}`} download={f.name} target="_blank" rel="noopener noreferrer"
                            className={`inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg border font-medium cursor-pointer hover:opacity-80 transition-opacity
                              ${msg.role === 'user'
                                ? 'bg-white/15 border-white/25 text-white'
                                : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'}`}
                            title={`Télécharger ${f.name}`}>
                            <span className="text-base leading-none">{icon}</span>
                            <span className="max-w-[120px] truncate">{f.name}</span>
                            {sizeKb && <span className="opacity-60">{sizeKb}Ko</span>}
                            <svg className="w-3 h-3 opacity-60 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                          </a>
                        ) : (
                          <div key={fi} className={`inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg border font-medium
                            ${msg.role === 'user'
                              ? 'bg-white/15 border-white/25 text-white'
                              : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'}`}>
                            <span className="text-base leading-none">{icon}</span>
                            <span className="max-w-[120px] truncate">{f.name}</span>
                            {sizeKb && <span className="opacity-60">{sizeKb}Ko</span>}
                          </div>
                        );
                    })}
                  </div>
                )}
                {msg.role === 'assistant' && msgMode === 'perplexity' && (
                  <div className="flex items-center gap-1.5 mb-1.5" data-testid={`web-indicator-${i}`}>
                    <Globe className="w-3.5 h-3.5 text-[#1D4E8A]" />
                    <span className="text-[11px] font-medium text-[#1D4E8A]">Recherche Web</span>
                  </div>
                )}
                <div className={`text-[15px] whitespace-pre-wrap leading-relaxed ${msg.role === 'user' ? 'text-white' : 'text-gray-800 dark:text-gray-100'}`}>
                  {msg.role === 'assistant' && msg.isSummary ? (
                    <ConversationSummaryCard summarizing={!!msg.summarizing} summary={msg.content} messageCount={msg.messageCount || 0} />
                  ) : msg.role === 'assistant' ? <MarkdownContent content={msg.content} /> : msg.content}
                </div>
                {msg.credits_exhausted && (
                  <div className="mt-3 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl" data-testid="credits-exhausted-banner">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-800/40 flex items-center justify-center flex-shrink-0">
                        <CreditCard className="w-5 h-5 text-amber-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-1">Crédits épuisés</p>
                        <p className="text-xs text-amber-700/80 dark:text-amber-300/70 mb-3">Ajoutez des crédits pour continuer à utiliser l'assistant IA.</p>
                        <button
                          onClick={() => { if (window.__openCreditsModal) window.__openCreditsModal(); }}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1D4E8A] text-white text-xs font-bold rounded-lg hover:bg-[#163d6e] transition-colors"
                          data-testid="buy-credits-btn"
                        >
                          <CreditCard className="w-3.5 h-3.5" />
                          Acheter des crédits
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                {msg.role === 'assistant' && msg.content && !(isStreaming && i === messages.length - 1) && (
                  <div className="flex items-center gap-2 mt-2">
                    <button onClick={() => copyMessage(msg.content)} className="p-1 hover:bg-[#1D4E8A]/10 rounded text-gray-500 hover:text-[#1D4E8A]" title="Copier" data-testid={`copy-msg-${i}`}>
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => saveToDrive(msg.content, 'text')} className="p-1 hover:bg-[#1D4E8A]/10 rounded text-gray-500 hover:text-[#1D4E8A]" title="Synchroniser sur le cloud" data-testid={`save-drive-${i}`}>
                      <Cloud className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => submitFeedback(i, 'up')} className={`p-1 rounded transition-colors ${feedbacks[String(i)] === 'up' ? 'bg-green-100 text-green-600' : 'hover:bg-[#1D4E8A]/10 text-gray-500 hover:text-[#1D4E8A]'}`} data-testid={`thumbsup-msg-${i}`}>
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => submitFeedback(i, 'down')} className={`p-1 rounded transition-colors ${feedbacks[String(i)] === 'down' ? 'bg-red-100 text-red-600' : 'hover:bg-[#1D4E8A]/10 text-gray-500 hover:text-[#1D4E8A]'}`} data-testid={`thumbsdown-msg-${i}`}>
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                    {/* Agent credit display */}
                    {(msg.isAgent || msg.mode === 'agent') && (msg.credit_cost > 0) && (
                      <span className="ml-auto text-[10px] font-medium text-gray-400 flex items-center gap-1" data-testid={`agent-credits-${i}`}>
                        <Sparkles className="w-3 h-3" /> -{msg.credit_cost} crédits
                      </span>
                    )}
                  </div>
                )}
                {msg.downloads && msg.downloads.length > 0 && (
                  <div className="flex flex-col gap-2 mt-3" data-testid={`downloads-${i}`}>
                    {msg.downloads.map((dl, di) => {
                      const fmt = (dl.format || dl.filename?.split('.').pop() || 'zip').toLowerCase();
                      const labels = {
                        zip: 'Télécharger le ZIP corrigé',
                        pdf: 'Télécharger le PDF',
                        docx: 'Télécharger le DOCX',
                        pptx: 'Télécharger la présentation',
                        xlsx: 'Télécharger le tableur Excel',
                        txt: 'Télécharger le fichier texte',
                        html: 'Télécharger le fichier HTML',
                        htm: 'Télécharger le fichier HTML',
                        md: 'Télécharger le Markdown',
                        json: 'Télécharger le JSON',
                        csv: 'Télécharger le CSV',
                      };
                      const label = labels[fmt] || `Télécharger (.${fmt})`;
                      const icons = {
                        zip: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>,
                        pdf: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>,
                      };
                      const icon = icons[fmt] || <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>;

                      const handleDownload = async (e) => {
                        e.preventDefault();
                        try {
                          const resp = await fetch(dl.url);
                          if (!resp.ok) throw new Error('Download failed');
                          const blob = await resp.blob();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = dl.filename || `fichier.${fmt}`;
                          document.body.appendChild(a);
                          a.click();
                          window.URL.revokeObjectURL(url);
                          a.remove();
                        } catch (err) {
                          console.error('Download error:', err);
                          window.open(dl.url, '_blank');
                        }
                      };

                      return (
                        <div key={di} className="rounded-xl border border-[#1D4E8A]/20 bg-[#EEF2FF] p-3 w-fit max-w-xs">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-8 h-8 bg-[#1D4E8A] rounded-lg flex items-center justify-center flex-shrink-0">
                              {icon}
                            </div>
                            <div>
                              <div className="text-[13px] font-semibold text-[#1D4E8A]">{dl.filename}</div>
                              {dl.corrected_files && (
                                <div className="text-[11px] text-[#1D4E8A]/70">{dl.corrected_files} fichier{dl.corrected_files > 1 ? 's' : ''} corrige{dl.corrected_files > 1 ? 's' : ''}</div>
                              )}
                            </div>
                          </div>
                          <button onClick={handleDownload}
                            className="flex items-center justify-center gap-2 w-full px-3 py-2 bg-[#1D4E8A] hover:bg-[#162d6b] text-white text-[12px] font-semibold rounded-lg transition-colors cursor-pointer"
                            data-testid={`download-btn-${i}-${di}`}>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                            {label}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
                {isStreaming && i === messages.length - 1 && msg.role === 'assistant' && msg.content && (
                  <div className="flex items-center gap-1.5 mt-2 text-[#1D4E8A]">
                    <div className="w-1.5 h-1.5 bg-[#1D4E8A] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-[#1D4E8A] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-[#1D4E8A] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    <span className="text-[10px] ml-1 text-gray-400 font-medium">en cours de redaction...</span>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 bg-gray-300 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1">
                  {(user?.name || 'U')[0].toUpperCase()}
                </div>
              )}
            </div>
            </React.Fragment>
            );
          })}
          {/* Manus polling animation (pre-WebSocket connection) - hidden when real agent steps arrive */}
          {manusPolling && agentSteps.length === 0 && (
            <div className="flex gap-3 items-start p-4 bg-white dark:bg-gray-800 rounded-2xl border border-[#1D4E8A]/10 shadow-sm" data-testid="manus-processing">
              <div className="relative shrink-0">
                <div className="w-10 h-10 bg-gradient-to-br from-[#1D4E8A] to-[#2563EB] rounded-xl flex items-center justify-center text-white shadow-lg">
                  <Bot className="w-5 h-5" style={{ animation: 'iconBreath 2s ease-in-out infinite' }} />
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#1D4E8A] rounded-full border-2 border-white">
                  <span className="absolute inset-0 bg-[#1D4E8A] rounded-full animate-ping opacity-60" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-[#1D4E8A] mb-2">Agent IA — Preparation...</div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Loader2 className="w-3 h-3 animate-spin text-[#1D4E8A]" />
                  <span>Initialisation de la tache</span>
                </div>
                <div className="mt-3 h-1 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-[#1D4E8A]/30 rounded-full" style={{ animation: 'indeterminate 1.8s ease-in-out infinite' }} />
                </div>
              </div>
              {cancelAgent && (
                <button onClick={cancelAgent}
                  className="px-2.5 py-1 text-[11px] font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors flex items-center gap-1 shrink-0"
                  data-testid="manus-cancel-btn">
                  <X className="w-3 h-3" /> Annuler
                </button>
              )}
              <style>{`
                @keyframes indeterminate { 0%{transform:translateX(-100%);width:40%} 100%{transform:translateX(300%);width:40%} }
                @keyframes iconBreath { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }
              `}</style>
            </div>
          )}
          {/* Manus IA-style Agent Animation */}
          {agentSteps.length > 0 && <AgentAnimation steps={agentSteps} onCancel={cancelAgent} isRunning={isStreaming} />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          onClick={() => { userScrolledUp.current = false; scrollContainerRef.current?.scrollTo({ top: scrollContainerRef.current.scrollHeight, behavior: 'smooth' }); }}
          className="absolute bottom-24 right-8 z-10 w-10 h-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full shadow-lg flex items-center justify-center text-gray-500 hover:text-[#1D4E8A] hover:border-[#1D4E8A] transition-all"
          data-testid="scroll-to-bottom-btn"
        >
          <ChevronDown className="w-5 h-5" />
        </button>
      )}

      {/* Input bar */}
      <div className="border-t border-[#E5E5E5] dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3 shrink-0">
        <div className="max-w-4xl mx-auto">
          {/* Complexity suggestion banner — amélioré */}
          {showComplexityHint && complexitySuggestion && (
            <div className="mb-2 flex items-center gap-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl px-3 py-2 animate-fadeIn" data-testid="complexity-suggestion-banner">
              <span className="text-base shrink-0" aria-hidden>&#128161;</span>
              <p className="flex-1 text-sm text-amber-800 dark:text-amber-200 min-w-0">
                {complexitySuggestion.level === 'agent'
                  ? 'Ce message semble complexe — passer en mode Agent IA ?'
                  : 'Ce message semble complexe — passer en mode Expert ?'
                }
              </p>
              <div className="flex items-center gap-1.5 shrink-0">
                {/* Bouton Changer — action directe */}
                {complexitySuggestion.level === 'agent' && mode !== 'agent' ? (
                  <button
                    onClick={() => { handleModeChange('agent'); setShowComplexityHint(false); }}
                    className="text-xs bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-lg font-semibold transition-colors"
                    data-testid="complexity-switch-agent"
                  >
                    Changer
                  </button>
                ) : complexitySuggestion.recommended_model && complexitySuggestion.recommended_model !== mode ? (
                  <button
                    onClick={() => { handleModeChange(complexitySuggestion.recommended_model); setShowComplexityHint(false); }}
                    className="text-xs bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-lg font-semibold transition-colors"
                    data-testid="complexity-switch-model"
                  >
                    Changer
                  </button>
                ) : null}
                {/* Bouton Ignorer — dismiss permanent pour cette session */}
                <button
                  onClick={() => {
                    setShowComplexityHint(false);
                    sessionStorage.setItem('zayado_complexity_dismissed', '1');
                  }}
                  className="text-xs text-amber-600 dark:text-amber-400 hover:text-amber-800 px-2 py-1.5 rounded-lg transition-colors"
                  data-testid="complexity-dismiss"
                >
                  Ignorer
                </button>
              </div>
            </div>
          )}
          {/* Attached files preview — amélioré avec icône, taille et indicateur d'analyse */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-1.5 px-3 py-2 mb-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-[#F5F5F0] dark:bg-gray-800">
              {attachedFiles.map((f, idx) => {
                const ext = (f.name || '').split('.').pop().toLowerCase();
                const fileIcons = { pdf: '📄', zip: '📦', docx: '📝', doc: '📝', xlsx: '📊', xls: '📊', png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', webp: '🖼️', txt: '📃', csv: '📊', mp4: '🎦', mp3: '🎵', md: '📋', json: '⚙️', html: '🌐', htm: '🌐', pptx: '📊', ppt: '📊' };
                const fileIcon = fileIcons[ext] || '📎';
                const sizeKb = f.size ? Math.round(f.size / 1024) : null;
                const hasExtract = f.extracted_text && f.extracted_text.length > 10;
                return (
                  <div key={idx} className="group flex items-center gap-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-2.5 py-1.5 text-[12px] text-gray-700 dark:text-gray-300 shadow-sm hover:border-[#1D4E8A]/40 transition-all">
                    <span className="text-[15px] leading-none">{fileIcon}</span>
                    <div className="flex flex-col min-w-0">
                      <span className="truncate max-w-[130px] font-medium">{f.name}</span>
                      <span className="text-[10px] text-gray-400">
                        {sizeKb ? (sizeKb > 1024 ? `${(sizeKb/1024).toFixed(1)} Mo` : `${sizeKb} Ko`) : ext.toUpperCase()}
                        {hasExtract && <span className="ml-1 text-green-600 font-medium">· Analysé</span>}
                      </span>
                    </div>
                    <button onClick={() => removeFile(idx)} className="ml-1 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all p-0.5 rounded" data-testid={`remove-file-${idx}`}>
                      <svg viewBox="0 0 16 16" className="w-3 h-3 fill-current"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>
                    </button>
                  </div>
                );
              })}
            </div>
          )}
          <div className="relative bg-white dark:bg-gray-800 border-[1.5px] border-[#E2DDD5] dark:border-gray-700 rounded-[14px] shadow-[0_1px_4px_rgba(0,0,0,0.04)] focus-within:border-[#1D4E8A] focus-within:shadow-[0_0_0_3px_rgba(29,78,138,0.08)] transition-all">
            {/* Toolbar INSIDE the input — Fichier, Image, Web, Dicter, Agent */}
            <div className="flex items-center gap-0.5 px-2 sm:px-3 pt-2 pb-0 border-b border-[#F5F3EF] overflow-x-auto" data-testid="input-toolbar-conv">
              <input ref={fileInputRef} type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.zip,.md,.json" className="hidden" onChange={handleFileUpload} data-testid="file-input" />
              <button onClick={() => fileInputRef.current?.click()} disabled={uploadingFile}
                className="flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800 transition-colors shrink-0"
                data-testid="chatbar-fichier-btn" title="Joindre un fichier">
                <Paperclip className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Fichier</span>
              </button>
              <button onClick={() => { if (imageMode) { setImageMode(false); } else { setImageMode(true); } inputRef.current?.focus(); }}
                className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${imageMode ? 'bg-[#0F1E3C] text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                data-testid="chatbar-image-btn" title="Generer une image">
                <Image className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Image</span>
              </button>
              <button onClick={() => { if (mode === 'perplexity') handleModeChange('fast'); else handleModeChange('perplexity'); inputRef.current?.focus(); }}
                className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${mode === 'perplexity' && !imageMode ? 'bg-[#0F1E3C] text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                data-testid="chatbar-web-btn" title="Recherche web">
                <Globe className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Web</span>
              </button>
              <div className="w-px h-4 bg-[#E2DDD5] mx-0.5 sm:mx-1 shrink-0" />
              <button onClick={toggleRecording}
                className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs transition-colors shrink-0 ${isRecording ? 'bg-red-500 text-white' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                data-testid="chatbar-dicter-btn" title={isRecording ? 'Arreter' : 'Dicter'}>
                {isRecording ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />} <span className="hidden sm:inline">Dicter</span>
              </button>
              <div className="ml-auto shrink-0">
                <button ref={agentToggleRef} onClick={toggleAgentPicker}
                  className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded-md text-xs font-medium transition-colors ${selectedAgent || agentActive ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'text-gray-500 hover:bg-[#F5F3EF] hover:text-[#1D4E8A]'}`}
                  data-testid="agent-toggle-btn" title={selectedAgent ? selectedAgent.name : 'Agent autonome'}>
                  <Bot className="w-3.5 h-3.5" /> <span className="hidden sm:inline">{selectedAgent ? selectedAgent.name : 'Agent autonome'}</span><span className="sm:hidden">{selectedAgent ? selectedAgent.name.slice(0, 5) : 'Agent'}</span>
                </button>
              </div>
            </div>
            {/* Agent Picker rendered via portal */}
            {/* Textarea */}
            <div className="relative">
              <textarea
                ref={inputRef}
                value={message}
                onChange={e => {
                  const val = e.target.value;
                  setMessage(val);
                  if (val.startsWith('/')) {
                    setShowSlashMenu(true);
                    setSlashActiveIdx(0);
                  } else {
                    setShowSlashMenu(false);
                  }
                }}
                onKeyDown={handleKeyDown}
                placeholder={selectedAgent ? `Parler à ${selectedAgent.name}...` : imageMode ? "Décrivez l'image souhaitée..." : agentActive ? "Décrivez la tâche pour l'agent..." : 'Rentabilité, clients, devis, organisation... (/ pour les commandes)'}
                rows={1}
                style={{ minHeight: '52px', maxHeight: '180px' }}
                className="w-full bg-transparent px-4 py-3 text-gray-900 dark:text-gray-100 placeholder-gray-400 resize-none focus:outline-none text-base leading-relaxed break-words"
                data-testid="chat-input-active"
              />
              {/* Slash command menu (vue conversation) */}
              {showSlashMenu && (
                <SlashCommandMenu
                  query={message}
                  activeIndex={slashActiveIdx}
                  setActiveIndex={setSlashActiveIdx}
                  onSelect={(cmd) => { setMessage(cmd); setShowSlashMenu(false); setSlashActiveIdx(0); inputRef.current?.focus(); }}
                  onClose={() => { setShowSlashMenu(false); setSlashActiveIdx(0); }}
                />
              )}
            </div>
            {/* Stop button removed — single stop button in bottom-right */}
            {/* Bottom: Sync + Send/Stop */}
            <div className="flex items-center justify-between px-3 pb-2 pt-0.5">
              <div className="flex items-center gap-2">
                <button onClick={handleSyncDrive} disabled={syncingDrive || autoSyncing}
                  className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors disabled:opacity-60 ${
                    (syncingDrive || autoSyncing) ? 'bg-blue-500 text-white border-blue-500' :
                    (driveConnected.google || driveConnected.onedrive) ? 'bg-[#1D4E8A] text-white border-[#1D4E8A]' :
                    'bg-white border-[#E2DDD5] text-gray-500 hover:bg-gray-100'
                  }`}
                  data-testid="sync-drive-persistent-btn">
                  {(syncingDrive || autoSyncing) ? <Loader2 className="w-3 h-3 animate-spin" /> :
                   (driveConnected.google || driveConnected.onedrive) ? <Cloud className="w-3 h-3" /> :
                   <CloudOff className="w-3 h-3" />}
                  {(syncingDrive || autoSyncing) ? 'Sync...' : (driveConnected.google || driveConnected.onedrive) ? 'Sync' : 'Cloud'}
                </button>
                <div className="relative" data-testid="prompts-dropdown-wrapper">
                  <button onClick={() => setShowPromptsDropdown(prev => !prev)}
                    className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors ${showPromptsDropdown ? 'bg-[#0F1E3C] text-white border-[#0F1E3C]' : 'border-[#E2DDD5] text-gray-500 hover:bg-[#F5F3EF] hover:text-gray-800'}`}
                    data-testid="chatbar-prompts-btn" title="Prompts rapides">
                    <Sparkles className="w-3 h-3" /> Prompts <ChevronDown className={`w-2.5 h-2.5 transition-transform ${showPromptsDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  {showPromptsDropdown && (
                    <div className="absolute bottom-full right-0 mb-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-40 max-h-96 overflow-y-auto animate-fadeIn" data-testid="prompts-dropdown-list">
                      {/* Header + bouton ajout */}
                      <div className="p-3 border-b border-gray-100 flex items-center justify-between">
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Prompts rapides</p>
                        <button onClick={() => setShowAddPrompt(prev => !prev)}
                          className="text-[10px] flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1E3A8A]/10 text-[#1E3A8A] hover:bg-[#1E3A8A]/20 transition-colors font-medium">
                          <Plus className="w-3 h-3" /> Nouveau
                        </button>
                      </div>
                      {/* Formulaire ajout */}
                      {showAddPrompt && (
                        <div className="p-3 border-b border-gray-100 bg-[#F8F9FF] space-y-2">
                          <input value={newPromptTitle} onChange={e => setNewPromptTitle(e.target.value)}
                            placeholder="Titre du prompt..." className="w-full text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-[#1E3A8A]" />
                          <textarea value={newPromptText} onChange={e => setNewPromptText(e.target.value)}
                            placeholder="Contenu du prompt..." rows={3}
                            className="w-full text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-[#1E3A8A] resize-none" />
                          <div className="flex items-center gap-2">
                            <select value={newPromptAction} onChange={e => setNewPromptAction(e.target.value)}
                              className="text-xs border border-gray-200 rounded-lg px-2 py-1 outline-none flex-1">
                              <option value="insert">Insert (coller)</option>
                              <option value="auto_send">Auto (envoyer)</option>
                            </select>
                            <button onClick={saveNewPrompt} disabled={savingPrompt || !newPromptTitle.trim() || !newPromptText.trim()}
                              className="text-xs px-3 py-1 bg-[#1E3A8A] text-white rounded-lg hover:bg-[#152F5C] disabled:opacity-40 transition-colors">
                              {savingPrompt ? '...' : 'Sauver'}
                            </button>
                          </div>
                        </div>
                      )}
                      {/* Section Prompts Extension IA (system) */}
                      {systemPrompts.length > 0 && (
                        <div>
                          <div className="px-3 pt-2.5 pb-1 flex items-center gap-1.5">
                            <span className="text-[9px] font-bold text-[#1E3A8A] uppercase tracking-wider bg-[#EEF2FF] px-1.5 py-0.5 rounded">Extension IA by Zayado</span>
                          </div>
                          <div className="px-1.5 pb-1">
                            {systemPrompts.map(p => (
                              <button key={p.id || p.title} onClick={() => { window.dispatchEvent(new CustomEvent('insertPrompt', { detail: { prompt: p.prompt, action: p.action } })); setShowPromptsDropdown(false); }}
                                className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-[#EEF2FF] text-left transition-colors">
                                <div className="flex-1 min-w-0"><span className="text-sm font-medium text-gray-800 truncate block">{p.title}</span><p className="text-[10px] text-gray-400 truncate mt-0.5">{p.prompt}</p></div>
                                <span className="text-[9px] px-1.5 py-0.5 rounded shrink-0 ml-2 bg-[#EEF2FF] text-[#1E3A8A] font-semibold">{p.action === 'auto_send' ? '⚡ Auto' : '⚡ Insert'}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Section Mes Prompts (user) */}
                      {userPrompts.length > 0 && (
                        <div>
                          <div className="px-3 pt-2.5 pb-1 flex items-center gap-1.5">
                            <span className="text-[9px] font-bold text-gray-500 uppercase tracking-wider bg-gray-100 px-1.5 py-0.5 rounded">✏️ Mes prompts</span>
                          </div>
                          <div className="px-1.5 pb-1">
                            {userPrompts.map(p => (
                              <button key={p.id || p.title} onClick={() => { window.dispatchEvent(new CustomEvent('insertPrompt', { detail: { prompt: p.prompt, action: p.action } })); setShowPromptsDropdown(false); }}
                                className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-[#F5F3EF] text-left transition-colors">
                                <div className="flex-1 min-w-0"><span className="text-sm font-medium text-gray-800 truncate block">{p.title}</span><p className="text-[10px] text-gray-400 truncate mt-0.5">{p.prompt}</p></div>
                                <span className={`text-[9px] px-1.5 py-0.5 rounded shrink-0 ml-2 ${p.action === 'auto_send' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-500'}`}>{p.action === 'auto_send' ? 'Auto' : 'Insert'}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      {systemPrompts.length === 0 && userPrompts.length === 0 && (
                        <div className="p-4 text-center">
                          <p className="text-xs text-gray-400">Aucun prompt configuré.</p>
                          <p className="text-[10px] text-gray-300 mt-1">Cliquez sur "+ Nouveau" pour en créer un.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {supportHumain.has && (
                  <button onClick={toggleSupportHumain}
                    className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full border transition-colors ${
                      supportHumain.active ? 'bg-green-50 border-green-300 text-green-700' : 'border-[#E2DDD5] text-gray-500 hover:text-green-600'
                    }`} data-testid="support-humain-toggle">
                    <Headphones className="w-3 h-3" /> {supportHumain.active ? 'Support actif' : 'Support'}
                  </button>
                )}
              </div>
              {isStreaming ? (
                <button onClick={handleAbort}
                  className="w-[34px] h-[34px] bg-red-500 hover:bg-red-600 rounded-[9px] flex items-center justify-center transition-colors animate-pulse"
                  data-testid="chat-stop-btn">
                  <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                </button>
              ) : (
                <button onClick={handleSend}
                  disabled={(!message.trim() && attachedFiles.length === 0)}
                  className="w-[34px] h-[34px] bg-[#0F1E3C] hover:bg-[#152F5C] disabled:opacity-30 rounded-[9px] flex items-center justify-center transition-colors"
                  data-testid="chat-send-active">
                  <Send className="w-4 h-4 text-white" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Support Humain Modal */}
      {supportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setSupportModalOpen(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[480px] mx-4 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="support-modal">
            <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Demande de support humain</h2>
              <button onClick={() => setSupportModalOpen(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-400"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-2">
                <div className="text-xs text-gray-400">Informations du chat</div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Conversation</span>
                  <span className="font-medium text-gray-800 dark:text-gray-100 truncate ml-4 max-w-[200px]">{'Conversation en cours'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Mode IA</span>
                  <span className="font-medium text-[#1D4E8A]">{currentMode?.label}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-300">Messages</span>
                  <span className="font-medium text-gray-800 dark:text-gray-100">{messages.length}</span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-200 block mb-2">Decrivez votre besoin</label>
                <textarea value={supportMessage} onChange={e => setSupportMessage(e.target.value)}
                  placeholder="Decrivez le probleme ou ce que vous souhaitez que notre equipe fasse..."
                  rows={3} className="w-full border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-xl p-3 text-sm resize-none focus:border-[#1D4E8A] focus:outline-none" data-testid="support-message" />
              </div>
              <p className="text-[11px] text-gray-400">En validant, les informations de ce chat seront transmises a notre equipe de support. Vous recevrez une reponse par email.</p>
            </div>
            <div className="border-t border-gray-100 dark:border-gray-700 p-5 flex justify-end gap-2">
              <button onClick={() => setSupportModalOpen(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">Annuler</button>
              <button onClick={submitSupportRequest} disabled={!supportMessage.trim()}
                className="px-5 py-2 bg-[#1D4E8A] text-white text-sm font-medium rounded-xl hover:bg-[#1D4E8A]/90 disabled:opacity-40 transition-colors" data-testid="support-submit-btn">
                Envoyer la demande
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BYOK API Key Modal */}
      {showByokModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowByokModal(false)} data-testid="byok-modal-overlay">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[440px] mx-4 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="byok-modal">
            <div className="p-6 text-center">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-[#1D4E8A]/10 flex items-center justify-center">
                <Key className="w-7 h-7 text-[#1D4E8A]" />
              </div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">Cle API OpenAI requise</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
                Pour utiliser le mode <strong>ChatGPT BYOK</strong>, vous devez d'abord configurer votre cle API OpenAI dans vos parametres.
              </p>
              <div className="bg-[#F5F5F0] dark:bg-gray-700 rounded-xl p-4 text-left mb-6 space-y-2">
                <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-bold text-[#1D4E8A] shrink-0">1.</span>
                  <span>Cliquez sur <strong>Paramètres</strong> (icône en bas à gauche)</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-bold text-[#1D4E8A] shrink-0">2.</span>
                  <span>Allez dans la section <strong>Clé API OpenAI</strong></span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-bold text-[#1D4E8A] shrink-0">3.</span>
                  <span>Collez votre cle (commence par <code className="bg-gray-200 dark:bg-gray-600 px-1 rounded text-xs">sk-...</code>)</span>
                </div>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowByokModal(false)} className="flex-1 px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-xl transition-colors" data-testid="byok-modal-cancel">
                  Annuler
                </button>
                <button onClick={() => { setShowByokModal(false); window.dispatchEvent(new CustomEvent('openSettingsTab', { detail: { tab: 'api' } })); }}
                  className="flex-1 px-4 py-2.5 bg-[#1D4E8A] text-white text-sm font-medium rounded-xl hover:bg-[#1D4E8A]/90 transition-colors flex items-center justify-center gap-2" data-testid="byok-modal-settings">
                  <Settings className="w-4 h-4" /> Ouvrir Paramètres
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent IA Confirmation Modal */}
      {showAgentConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => { setShowAgentConfirm(false); setPendingAgentMessage(null); }} data-testid="agent-confirm-overlay">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[460px] mx-4 overflow-hidden" onClick={e => e.stopPropagation()} data-testid="agent-confirm-modal">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Confirmer la tache Agent IA</h2>
                  <p className="text-xs text-gray-500">Verification avant execution</p>
                </div>
              </div>

              <div className="bg-[#F5F5F0] dark:bg-gray-700 rounded-xl p-4 mb-4 space-y-3">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  <div className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Vos credits</div>
                  <div className="flex items-center justify-between py-1.5 border-b border-gray-200/60 dark:border-gray-600">
                    <span>Credits disponibles</span>
                    <span className="font-bold text-[#1D4E8A]">{user?.credits || 0}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-gray-200/60 dark:border-gray-600">
                    <span>Chat IA (Claude, Gemini...)</span>
                    <span className="text-gray-500">2-4 credits/msg</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5">
                    <span className="flex items-center gap-1">Agent IA <AlertTriangle className="w-3 h-3 text-amber-500" /></span>
                    <span className="font-semibold text-amber-600">60-600 credits/tache</span>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4 mb-6">
                <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
                  Cette tache consommera environ <strong>150 credits</strong>
                  {user?.credits > 0 && (
                    <span> (soit <strong>{Math.round((150 / (user?.credits || 1)) * 100)}%</strong> de vos credits disponibles)</span>
                  )}. Confirmer ?
                </p>
              </div>

              <div className="flex gap-3">
                <button onClick={() => { setShowAgentConfirm(false); setPendingAgentMessage(null); }}
                  className="flex-1 px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-xl transition-colors" data-testid="agent-confirm-cancel">
                  Annuler
                </button>
                <button onClick={() => { setShowAgentConfirm(false); handleSend(); }}
                  className="flex-1 px-4 py-2.5 bg-[#1D4E8A] text-white text-sm font-medium rounded-xl hover:bg-[#1D4E8A]/90 transition-colors flex items-center justify-center gap-2" data-testid="agent-confirm-proceed">
                  <Bot className="w-4 h-4" /> Lancer la tache
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===== MODAL TRANSFERT DE MODE ===== */}
      {modeTransferDialog && (() => {
        const allModes = [...(mainModes(lang) || []), ...(extraModes(lang) || [])];
        const targetMode = allModes.find(m => m.id === modeTransferDialog.pendingMode);
        const targetLabel = modeTransferDialog.pendingImageMode ? 'Image IA' : (targetMode?.label || modeTransferDialog.pendingMode);
        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
            onClick={() => setModeTransferDialog(null)}>
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-[360px] mx-4 overflow-hidden"
              onClick={e => e.stopPropagation()}>
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[#EEF2FF] flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-[#1D4E8A]" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Changer de mode</h2>
                    <p className="text-xs text-gray-500">Basculer vers <strong className="text-[#1D4E8A]">{targetLabel}</strong></p>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-300 mb-5">
                  Voulez-vous conserver le contexte de la conversation actuelle dans le nouveau mode ?
                </p>

                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={() => applyModeChange(modeTransferDialog.pendingMode, modeTransferDialog.pendingImageMode, true)}
                    className="w-full px-4 py-3 bg-[#1D4E8A] text-white text-sm font-semibold rounded-xl hover:bg-[#152C6B] transition-colors flex items-center gap-2">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
                    Conserver l'historique
                    <span className="ml-auto text-xs opacity-70 font-normal">Contexte transféré</span>
                  </button>
                  <button
                    onClick={() => applyModeChange(modeTransferDialog.pendingMode, modeTransferDialog.pendingImageMode, false)}
                    className="w-full px-4 py-3 bg-[#F5F5F0] dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm font-semibold rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center gap-2">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12l7-7 7 7"/></svg>
                    Nouvelle conversation
                    <span className="ml-auto text-xs opacity-60 font-normal">Repartir à zéro</span>
                  </button>
                  <button
                    onClick={() => setModeTransferDialog(null)}
                    className="w-full px-4 py-2 text-xs text-gray-400 hover:text-gray-600 transition-colors">
                    Annuler
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
      
      {/* Sync prompt removed — controlled via Settings → Synchronisation */}

      {/* Task Complete Animation */}
      <TaskCompleteAnimation
        show={showTaskComplete}
        taskType={taskCompleteData.taskType}
        message={taskCompleteData.message}
        creditsUsed={taskCompleteData.creditsUsed}
        onComplete={() => setShowTaskComplete(false)}
        duration={3500}
      />

      {/* Agent Picker Portal — rendered outside overflow containers */}
      {showAgentPicker && createPortal(
        <div
          className="fixed w-56 max-h-72 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-1.5 animate-fadeIn"
          style={{ top: Math.max(8, agentPickerPos.top - 300), left: agentPickerPos.left, zIndex: 9999 }}
          data-testid="agent-picker-dropdown"
        >
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-2 mb-1">Choisir un agent</p>
          <button onClick={() => { setSelectedAgent(null); setShowAgentPicker(false); }}
            className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors ${!selectedAgent ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200'}`}
            data-testid="agent-pick-default">
            <Sparkles className="w-4 h-4" />
            <div>
              <span className="text-sm font-semibold">Extension IA by Zayado</span>
              <p className="text-[10px] text-gray-400">Assistant par defaut</p>
            </div>
          </button>
          {customAgents.map(agent => (
            <button key={agent.id} onClick={() => selectAgent(agent)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors ${selectedAgent?.id === agent.id ? 'bg-[#1D4E8A]/10 text-[#1D4E8A]' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200'}`}
              data-testid={`agent-pick-${agent.id}`}>
              <div className="w-4 h-4 rounded-full shrink-0" style={{ background: agent.color || '#1D4E8A' }} />
              <div className="min-w-0">
                <span className="text-sm font-semibold truncate block">{agent.name}</span>
                <p className="text-[10px] text-gray-400 truncate">{agent.system_prompt?.slice(0, 40) || 'Agent personnalise'}</p>
              </div>
            </button>
          ))}
          {customAgents.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-2">Aucun agent. Creez-en dans Parametres.</p>
          )}
        </div>,
        document.body
      )}
    </div>
  );
};

export default ChatInterface;
