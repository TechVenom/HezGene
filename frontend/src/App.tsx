import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dna, FolderCode,
  Settings, LayoutDashboard, FlaskConical, BookOpen, Activity,
  ChevronDown, ChevronRight, PanelLeftClose, PanelLeft, AlertTriangle
} from 'lucide-react';
import { getHealth } from './api';

import Dashboard from './pages/Dashboard';
import EvolutionArena from './pages/EvolutionArena';
import CodeManager from './pages/CodeManager';
import DNAExplorer from './pages/DNAExplorer';
import HistoryPage from './pages/History';
import SettingsPage from './pages/Settings';
import Docs from './pages/Docs';
import Status from './pages/Status';

const navStructure = [
  {
    type: 'link',
    to: '/',
    icon: LayoutDashboard,
    label: 'Home',
  },
  {
    type: 'collapsible',
    id: 'code-evolution',
    icon: FolderCode,
    label: 'Code Evolution',
    items: [
      { to: '/files', label: 'Code Manager' },
      { to: '/arena', label: 'Evolution Arena' },
      { to: '/dna', label: 'DNA Explorer' },
      { to: '/history', label: 'Battle History' },
    ]
  },
  {
    type: 'header',
    label: 'HezGene apps'
  },
  {
    type: 'link',
    to: '/status',
    icon: Activity,
    label: 'System Status',
  },
  {
    type: 'header',
    label: 'Documentation'
  },
  {
    type: 'link',
    to: '/docs',
    icon: BookOpen,
    label: 'API & Usagent Docs'
  }
];

function SidebarNavigation({ collapsed }: { collapsed: boolean }) {
  const location = useLocation();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'code-evolution': true,
  });

  const toggleSection = (id: string) => {
    setExpandedSections(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderItem = (item: any) => {
    if (item.type === 'header') {
      if (collapsed) {
        return (
          <div key={item.label} className="mx-auto my-3 w-6 h-px bg-border" />
        );
      }
      return (
        <div key={item.label} className="px-4 pt-5 pb-2">
          <span className="text-[11px] font-bold text-text-secondary uppercase tracking-wider">{item.label}</span>
        </div>
      );
    }

    if (item.type === 'link') {
      const isActive = location.pathname === item.to;
      const Icon = item.icon;

      if (collapsed) {
        return (
          <Link key={item.to} to={item.to} className="block px-2 mb-0.5" title={item.label}>
            <div className={`flex items-center justify-center p-2.5 rounded-lg transition-colors ${
              isActive ? 'bg-[#f3f4f6] text-[#111827]' : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
            }`}>
              <Icon size={20} className={isActive ? 'text-[#111827]' : 'text-text-secondary'} />
            </div>
          </Link>
        );
      }

      return (
        <Link key={item.to} to={item.to} className="block px-2 mb-0.5">
          <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
            isActive ? 'bg-[#f3f4f6] text-[#111827] font-semibold' : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary font-medium'
          }`}>
            <Icon size={18} className={isActive ? 'text-[#111827]' : 'text-text-secondary'} />
            <span className="text-[14px] flex-1">{item.label}</span>
          </div>
        </Link>
      );
    }

    if (item.type === 'collapsible') {
      const isExpanded = expandedSections[item.id];
      const Icon = item.icon;
      const hasActiveChild = item.items.some((subItem: any) => location.pathname === subItem.to);

      if (collapsed) {
        // In collapsed mode, show parent icon + sub-item icons on hover via a tooltip-like popout
        return (
          <div key={item.id} className="px-2 mb-0.5 relative group">
            <div className={`flex items-center justify-center p-2.5 rounded-lg transition-colors cursor-pointer ${
              hasActiveChild ? 'bg-[#f3f4f6] text-[#111827]' : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
            }`}>
              <Icon size={20} className={hasActiveChild ? 'text-[#111827]' : 'text-text-secondary'} />
            </div>
            {/* Flyout menu on hover */}
            <div className="absolute left-full top-0 ml-1 hidden group-hover:block z-50">
              <div className="bg-white border border-border rounded-xl shadow-lg py-2 px-1 min-w-[180px]">
                <div className="px-3 py-1.5 text-[11px] font-bold text-text-secondary uppercase tracking-wider">
                  {item.label}
                </div>
                {item.items.map((subItem: any) => {
                  const isSubActive = location.pathname === subItem.to;
                  return (
                    <Link key={subItem.to} to={subItem.to} className="block">
                      <div className={`px-3 py-2 rounded-lg text-[13px] transition-colors ${
                        isSubActive ? 'text-[#111827] font-semibold bg-[#f3f4f6]' : 'text-text-secondary font-medium hover:text-[#111827] hover:bg-[#f3f4f6]/50'
                      }`}>
                        {subItem.label}
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        );
      }

      return (
        <div key={item.id} className="px-2 mb-0.5">
          <button
            onClick={() => toggleSection(item.id)}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors ${
              (hasActiveChild || isExpanded) ? 'bg-[#f3f4f6] text-[#111827] font-semibold' : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary font-medium'
            }`}
          >
            <div className="flex items-center gap-3">
              <Icon size={18} className={(hasActiveChild || isExpanded) ? 'text-[#111827]' : 'text-text-secondary'} />
              <span className="text-[14px]">{item.label}</span>
            </div>
            {isExpanded ? <ChevronDown size={14} className="text-text-secondary opacity-70" /> : <ChevronRight size={14} className="text-text-secondary opacity-70" />}
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-1 ml-[11px] pl-5 border-l-[1.5px] border-border flex flex-col space-y-0.5 py-1">
                  {item.items.map((subItem: any) => {
                    const isSubActive = location.pathname === subItem.to;
                    return (
                      <Link key={subItem.to} to={subItem.to} className="relative group block">
                        <div className={`px-3 py-1.5 rounded-lg flex items-center justify-between transition-colors ${
                          isSubActive ? 'text-[#111827] font-semibold bg-[#f3f4f6]/60' : 'text-text-secondary font-medium hover:text-[#111827] hover:bg-[#f3f4f6]/50'
                        }`}>
                          <span className="text-[14px]">{subItem.label}</span>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    }
    return null;
  };

  return (
    <nav className="flex-1 space-y-0.5 overflow-y-auto pb-4">
      {navStructure.map(renderItem)}
    </nav>
  );
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [serverDegraded, setServerDegraded] = useState(false);

  useEffect(() => {
    // Initial check
    getHealth().then((data) => setServerDegraded(data.status !== 'alive')).catch(() => setServerDegraded(true));
    
    // Poll every 10 seconds
    const interval = setInterval(async () => {
      try {
        const data = await getHealth();
        setServerDegraded(data.status !== 'alive');
      } catch (e) {
        setServerDegraded(true);
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Router>
      <div className="flex h-screen bg-bg-primary text-text-primary overflow-hidden font-sans selection:bg-accent-purple/30">
        {/* Sidebar */}
        <motion.aside
          animate={{ width: sidebarCollapsed ? 68 : 256 }}
          transition={{ duration: 0.25, ease: 'easeInOut' }}
          className="flex-shrink-0 border-r border-border bg-bg-secondary flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-20 overflow-hidden"
        >
          {/* Logo + Toggle */}
          <div className={`flex items-center justify-between ${sidebarCollapsed ? 'p-3' : 'p-5 pb-2'}`}>
            {sidebarCollapsed ? (
              <Link to="/" className="mx-auto" title="HezGene">
                <Dna className="text-accent-purple" size={26} />
              </Link>
            ) : (
              <Link to="/" className="flex items-center gap-2.5 group">
                <div className="relative">
                  <Dna
                    className="text-accent-purple transition-transform duration-500 group-hover:rotate-180"
                    size={28}
                  />
                  <div className="absolute inset-0 blur-md bg-accent-purple/20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div>
                  <h1 className="text-xl font-bold tracking-tight text-text-primary font-display">
                    HezGene
                  </h1>
                  <p className="text-[10px] text-text-secondary tracking-widest uppercase font-medium">
                    The DNA of Software
                  </p>
                </div>
              </Link>
            )}
          </div>

          {/* Toggle Button */}
          <div className={`flex ${sidebarCollapsed ? 'justify-center px-2' : 'justify-end px-4'} mb-1`}>
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-1.5 rounded-lg text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
            </button>
          </div>

          {/* Divider */}
          <div className={`${sidebarCollapsed ? 'mx-3' : 'mx-4'} my-1 h-px bg-gradient-to-r from-transparent via-border to-transparent`} />

          {/* Navigation */}
          <SidebarNavigation collapsed={sidebarCollapsed} />

          {/* Bottom nav */}
          <div className={`${sidebarCollapsed ? 'px-2' : 'px-3'} pb-4 space-y-1`}>
            <div className={`${sidebarCollapsed ? 'mx-2' : 'mx-1'} mb-2 h-px bg-gradient-to-r from-transparent via-border to-transparent`} />
            
            {sidebarCollapsed ? (
              <Link to="/settings" className="block px-2 mb-0.5" title="Settings">
                <div className="flex items-center justify-center p-2.5 rounded-lg transition-colors text-text-secondary hover:bg-bg-tertiary hover:text-text-primary">
                  <Settings size={20} className="text-text-secondary" />
                </div>
              </Link>
            ) : (
              <Link to="/settings" className="block px-2 mb-0.5">
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-text-secondary hover:bg-bg-tertiary hover:text-text-primary font-medium">
                  <Settings size={18} className="text-text-secondary" />
                  <span className="text-[14px] flex-1">Settings</span>
                </div>
              </Link>
            )}

            {/* Version badge */}
            {!sidebarCollapsed && (
              <div className="flex items-center gap-2 px-4 py-2 mt-2">
                <FlaskConical size={12} className="text-accent-cyan/60" />
                <span className="text-[10px] text-text-secondary/60 font-mono">v1.0.0 — prototype</span>
              </div>
            )}
          </div>
        </motion.aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col bg-bg-primary relative overflow-hidden">
          <AnimatePresence>
            {serverDegraded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="bg-accent-red/10 border-b border-accent-red/20 text-accent-red px-4 py-2 flex items-center justify-center gap-2 text-sm font-medium z-50 shrink-0"
              >
                <AlertTriangle size={16} />
                Server connection lost or degraded. Attempting to reconnect...
              </motion.div>
            )}
          </AnimatePresence>

          <div className="relative z-10 flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/arena" element={<EvolutionArena />} />
              <Route path="/files" element={<CodeManager />} />
              <Route path="/dna" element={<DNAExplorer />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/status" element={<Status />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/docs" element={<Docs />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
