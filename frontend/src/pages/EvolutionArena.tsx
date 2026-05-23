import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Shield, Cpu, Trophy, Swords, Dna, Zap, Activity,
  CheckCircle2, XCircle, ArrowRight, Eye, Rocket, Clock,
  MemoryStick, BookOpen, Bug, Lock, Plus, Code, Sparkles, Settings,
  ArrowLeft, AlertCircle, RefreshCw
} from 'lucide-react';
import { getFiles, getFileDetails, deployEvolvedCode } from '../api';
import { useEvolution } from '../hooks/useEvolution';
import ProjectEvolutionArena from './ProjectEvolutionArena';

const STRATEGY_LABELS: Record<string, { label: string, color: string, bg: string, icon: any, emoji: string }> = {
  'loop_to_comprehension': { label: 'Loop → Comprehension', color: 'text-accent-cyan', bg: 'bg-accent-cyan/10', icon: Code, emoji: '🔄' },
  'combine_operations': { label: 'Combine Operations', color: 'text-accent-purple', bg: 'bg-accent-purple/10', icon: Plus, emoji: '🔗' },
  'guard_clause': { label: 'Guard Clause', color: 'text-accent-green', bg: 'bg-accent-green/10', icon: Shield, emoji: '🛡️' },
  'dead_code_remove': { label: 'Dead Code Removal', color: 'text-accent-red', bg: 'bg-accent-red/10', icon: AlertCircle, emoji: '🗑️' },
  'constant_fold': { label: 'Constant Folding', color: 'text-accent-yellow', bg: 'bg-accent-yellow/10', icon: Settings, emoji: '📐' },
  'early_return': { label: 'Early Return', color: 'text-accent-yellow', bg: 'bg-accent-yellow/10', icon: Zap, emoji: '⚡' },
  'augmented_assign': { label: 'Augmented Assignment', color: 'text-accent-purple', bg: 'bg-accent-purple/10', icon: Plus, emoji: '➕' },
  'llm': { label: 'LLM Optimization', color: 'text-accent-cyan', bg: 'bg-accent-cyan/10', icon: Sparkles, emoji: '🤖' },
  'unknown': { label: 'Unknown Strategy', color: 'text-text-secondary', bg: 'bg-bg-tertiary', icon: Settings, emoji: '❓' }
};

const MutantBadge = ({ strategy }: { strategy: string }) => {
  // Try to match the exact strategy or prefix (like llm_0_some_strategy -> llm)
  let meta = STRATEGY_LABELS[strategy];
  if (!meta && strategy.includes('llm')) {
    meta = STRATEGY_LABELS['llm'];
  }
  meta = meta || STRATEGY_LABELS['unknown'];
  
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md ${meta.bg} ${meta.color} border border-current/20 shadow-sm whitespace-nowrap`}>
      {Icon && <Icon size={10} />}
      <span className="font-bold text-[9px] uppercase tracking-wider">{meta.label || strategy}</span>
    </span>
  );
};

function InfoTooltip({ content }: { content: string }) {
  const [show, setShow] = useState(false);
  return (
    <span className="relative inline-flex items-center ml-1.5 group select-none">
      <button
        type="button"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={(e) => { e.preventDefault(); setShow(!show); }}
        className="w-4 h-4 rounded-full bg-bg-tertiary hover:bg-accent-purple/20 text-text-secondary hover:text-accent-purple inline-flex items-center justify-center text-[10px] font-bold border border-border/40 transition-colors cursor-help"
      >
        ?
      </button>
      <AnimatePresence>
        {show && (
          <motion.span
            initial={{ opacity: 0, y: 5, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 5, scale: 0.95 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-bg-secondary border border-border text-xs rounded-xl shadow-xl z-50 text-text-primary pointer-events-none text-center font-normal normal-case block"
            style={{ originY: 1 }}
          >
            <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-bg-secondary block" />
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}

function MutantCard({ mutant, isWinner }: { mutant: any; isWinner: boolean }) {
  let info = STRATEGY_LABELS[mutant.strategy];
  if (!info && mutant.strategy.includes('llm')) info = STRATEGY_LABELS['llm'];
  info = info || STRATEGY_LABELS['unknown'];
  
  const passed = mutant.passed === true;
  const failed = mutant.disqualified === true;
  const hasScore = mutant.score !== undefined;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className={`rounded-xl border p-4 transition-all ${
        isWinner ? 'border-accent-yellow/60 bg-accent-yellow/5 glow-yellow animate-scale-in' :
        failed ? 'border-accent-red/30 bg-accent-red/5 opacity-60' :
        passed ? 'border-accent-green/30 bg-accent-green/5' :
        'border-border/50 bg-bg-tertiary/30'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{info.emoji}</span>
          <span className="text-sm font-bold">{info.label}</span>
        </div>
        {isWinner && <Trophy size={16} className="text-accent-yellow animate-trophy" />}
        {failed && <XCircle size={16} className="text-accent-red" />}
        {passed && !isWinner && <CheckCircle2 size={16} className="text-accent-green" />}
      </div>

      {hasScore && (
        <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
          <div className="flex items-center gap-1 text-text-secondary">
            <Zap size={11} /> Score:
            <span className={`font-bold ${mutant.score > 50 ? 'text-accent-green' : 'text-accent-yellow'}`}>
              {mutant.score?.toFixed(1)}
            </span>
          </div>
          <div className="flex items-center gap-1 text-text-secondary">
            <Clock size={11} /> Speed:
            <span className="font-bold text-text-primary">{mutant.speed_ms?.toFixed(3)}ms</span>
          </div>
          <div className="flex items-center gap-1 text-text-secondary">
            <MemoryStick size={11} /> Mem:
            <span className="font-bold text-text-primary">{mutant.memory_bytes}B</span>
          </div>
          <div className="flex items-center gap-1 text-text-secondary">
            <BookOpen size={11} /> Read:
            <span className="font-bold text-text-primary">{mutant.readability?.toFixed(1)}</span>
          </div>
        </div>
      )}

      {failed && mutant.disqualify_reason && (
        <p className="text-xs text-accent-red/80 mt-2 truncate">{mutant.disqualify_reason}</p>
      )}
    </motion.div>
  );
}

export default function EvolutionArena() {
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(1);
  const [files, setFiles] = useState<any[]>([]);
  const [functions, setFunctions] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState(searchParams.get('target') || '');
  const [selectedFunc, setSelectedFunc] = useState(searchParams.get('target') === '.' ? 'ALL' : '');
  
  // Settings configs
  const [useAST, setUseAST] = useState(true);
  const [useLLM, setUseLLM] = useState(false);
  const [applyMode, setApplyMode] = useState(false);
  const [generations, setGenerations] = useState(5);
  
  const [showCode, setShowCode] = useState(true);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployError, setDeployError] = useState<string | null>(null);
  const [deploySuccess, setDeploySuccess] = useState(false);
  const [deployingBatch, setDeployingBatch] = useState<Record<string, 'loading' | 'success' | 'error'>>({});
  const logRef = useRef<HTMLDivElement>(null);

  const evo = useEvolution();

  // Load files
  useEffect(() => {
    getFiles().then((res) => res.data && setFiles(res.data)).catch(() => {});
  }, []);

  // Load functions for selected file
  useEffect(() => {
    if (!selectedFile) { setFunctions([]); return; }
    getFileDetails(selectedFile)
      .then((res) => {
        if (res.data?.functions) {
          // Only show evolvable/unfrozen functions
          setFunctions(res.data.functions.filter((f: any) => f.evolvable));
        }
      })
      .catch(() => setFunctions([]));
  }, [selectedFile]);

  // Synchronize step based on evolution progress
  useEffect(() => {
    if (evo.isRunning) {
      setStep(3);
    } else if (evo.winner || evo.stage === 'complete' || evo.stage === 'no_improvement') {
      setStep(4);
    }
  }, [evo.isRunning, evo.winner, evo.stage]);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [evo.messages]);

  const handleStart = () => {
    if (!selectedFile || !selectedFunc) return;
    setDeploySuccess(false);
    setDeployError(null);
    
    evo.start({
      file_id: selectedFile,
      function_name: selectedFunc === 'ALL' ? undefined : selectedFunc,
      use_llm: useLLM,
      apply: applyMode,
      generations: generations,
    });
  };

  const handleManualDeploy = async () => {
    if (!evo.winner || !selectedFile || !selectedFunc) return;
    setIsDeploying(true);
    setDeployError(null);
    setDeploySuccess(false);
    try {
      const target = `${selectedFile}:${selectedFunc}`;
      await deployEvolvedCode(target);
      setDeploySuccess(true);
    } catch (err: any) {
      setDeployError(err.message || 'Deployment failed');
    } finally {
      setIsDeploying(false);
    }
  };

  const handleBatchDeploy = async (funcName: string) => {
    if (!selectedFile) return;
    setDeployingBatch((prev) => ({ ...prev, [funcName]: 'loading' }));
    try {
      const target = `${selectedFile}:${funcName}`;
      await deployEvolvedCode(target);
      setDeployingBatch((prev) => ({ ...prev, [funcName]: 'success' }));
    } catch (err: any) {
      setDeployingBatch((prev) => ({ ...prev, [funcName]: 'error' }));
    }
  };

  const handleReset = () => {
    evo.reset();
    setStep(1);
    setDeploySuccess(false);
    setDeployError(null);
    setDeployingBatch({});
  };

  const currentFuncObj = functions.find((f) => f.qualified_name === selectedFunc);
  const winnerStrategy = evo.winner?.strategy || '';

  // If evolving a full file or project, render the project evolution view
  if (selectedFunc === 'ALL' || selectedFile === '.') {
    return <ProjectEvolutionArena target={selectedFile} />;
  }

  // Setup Wizard Steps Definitions
  const stepsList = [
    { id: 1, name: 'Target Selection', description: 'Choose function to evolve' },
    { id: 2, name: 'Settings Configuration', description: 'Optimize mutation engine' },
    { id: 3, name: 'Live Combat Arena', description: 'Gauntlet & tournament' },
    { id: 4, name: 'Promotion & Results', description: 'Apply improved code' },
  ];

  return (
    <div className="p-6 min-h-screen flex flex-col">
      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold font-display gradient-yellow-red">Evolution Arena</h2>
          <p className="text-text-secondary text-sm mt-0.5">Automated genetic refactoring for high-performance software</p>
        </div>
        {evo.isRunning && (
          <div className="flex items-center gap-2 bg-accent-green/10 border border-accent-green/30 px-3 py-1 rounded-full text-accent-green text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-green opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-green" />
            </span>
            EVOLUTION IN PROGRESS
          </div>
        )}
      </header>

      {/* Step Tracker */}
      <div className="mb-8 rounded-xl border border-border bg-white shadow-sm p-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          {stepsList.map((s, idx) => {
            const isCompleted = step > s.id;
            const isActive = step === s.id;
            const isClickable = !evo.isRunning && s.id < step;
            return (
              <div key={s.id} className="flex-1 w-full flex items-center gap-3">
                <button
                  type="button"
                  disabled={!isClickable}
                  onClick={() => isClickable && setStep(s.id)}
                  className={`flex items-center justify-center w-8 h-8 rounded-full border font-bold text-xs transition-all ${
                    isCompleted ? 'bg-accent-green/20 border-accent-green text-accent-green hover:bg-accent-green/30 cursor-pointer' :
                    isActive ? 'bg-accent-purple text-white border-accent-purple shadow-md' :
                    'bg-bg-tertiary border-border text-text-secondary/60'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 size={14} /> : s.id}
                </button>
                <div 
                  className={`flex-1 min-w-0 ${isClickable ? 'cursor-pointer hover:opacity-80' : ''}`}
                  onClick={() => isClickable && setStep(s.id)}
                >
                  <p className={`text-xs font-bold leading-none ${isActive ? 'text-text-primary' : 'text-text-secondary/70'}`}>{s.name}</p>
                  <p className="text-[10px] text-text-secondary/50 mt-1 truncate">{s.description}</p>
                </div>
                {idx < stepsList.length - 1 && (
                  <ArrowRight size={14} className="hidden md:block text-text-secondary/20 mx-2" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Wizard Content Card */}
      <div className="flex-1 flex flex-col min-h-0">
        <AnimatePresence mode="wait">
          {/* STEP 1: TARGET SELECTOR */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6"
            >
              {/* Left Column: Dropdowns */}
              <div className="lg:col-span-2 rounded-2xl border border-border bg-white shadow-sm p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-bold font-display text-text-primary mb-2">Step 1: Select Evolved Code Target</h3>
                  <p className="text-text-secondary text-xs mb-6">
                    Select a Python file from your workspace, then select the target function to optimize. 
                    HezGene will read its AST, extract its genetic profile (DNA), and measure its baseline performance in the arena.
                  </p>

                  <div className="space-y-5">
                    <div>
                      <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                        Target File
                        <InfoTooltip content="Select a Python source file from the workspace that you wish to analyze and evolve." />
                      </label>
                      <select
                        className="w-full bg-bg-tertiary border border-border/60 rounded-xl p-3 text-sm text-text-primary focus:outline-none focus:border-accent-purple/60 transition-colors"
                        value={selectedFile}
                        onChange={(e) => { setSelectedFile(e.target.value); setSelectedFunc(''); }}
                      >
                        <option value="">Select a file...</option>
                        <option value="." className="font-bold text-accent-purple">Project Workspace (Global)</option>
                        {files.map((f: any) => (
                          <option key={f.id} value={f.id}>{f.name} ({f.functions} functions)</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                        Function target
                        <InfoTooltip content="Select the specific function or class method to mutate and evaluate. The evolution is safely isolated to this function only." />
                      </label>
                      <select
                        className="w-full bg-bg-tertiary border border-border/60 rounded-xl p-3 text-sm text-text-primary focus:outline-none focus:border-accent-purple/60 transition-colors"
                        value={selectedFunc}
                        onChange={(e) => setSelectedFunc(e.target.value)}
                        disabled={!selectedFile}
                      >
                        <option value="" disabled>Select a function...</option>
                        {functions.length > 0 && <option value="ALL">All Functions (Batch Evolution)</option>}
                        {functions.map((f: any) => (
                          <option key={f.qualified_name} value={f.qualified_name}>{f.qualified_name} ({f.lines} LOC)</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-4 border-t border-border/20 flex justify-end">
                  <motion.button
                    whileHover={selectedFunc ? { scale: 1.02 } : {}}
                    whileTap={selectedFunc ? { scale: 0.98 } : {}}
                    disabled={!selectedFunc}
                    onClick={() => setStep(2)}
                    className={`px-6 py-3 rounded-xl font-bold text-sm flex items-center gap-2 transition-all ${
                      selectedFunc
                        ? 'bg-accent-purple text-white shadow-lg shadow-accent-purple/20 hover:bg-accent-purple/90'
                        : 'bg-bg-tertiary text-text-secondary/40 cursor-not-allowed border border-border/30'
                    }`}
                  >
                    Configure Evolution Settings <ArrowRight size={16} />
                  </motion.button>
                </div>
              </div>

              {/* Right Column: DNA Profile Sidebar */}
              <div className="lg:col-span-1 rounded-2xl border border-border bg-white shadow-sm p-6 flex flex-col justify-between">
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-text-secondary mb-4 flex items-center gap-1.5">
                    <Dna size={14} className="text-accent-purple" /> Target DNA Profile
                  </h4>

                  {currentFuncObj ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl bg-bg-primary/50 border border-border/30">
                        <p className="text-[10px] text-text-secondary uppercase tracking-widest">Target Name</p>
                        <p className="text-sm font-bold text-text-primary mt-1 break-all">{currentFuncObj.qualified_name}</p>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3.5 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Size (LOC)
                            <InfoTooltip content="Total raw lines of code representing this function body." />
                          </p>
                          <p className="text-lg font-bold text-accent-cyan mt-0.5">{currentFuncObj.lines}</p>
                        </div>
                        <div className="p-3.5 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Evolved
                            <InfoTooltip content="Number of times this function has successfully evolved in previous sessions." />
                          </p>
                          <p className="text-lg font-bold text-accent-green mt-0.5">{currentFuncObj.evolution_count ?? 0}x</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Time Complex.
                          </p>
                          <p className="text-sm font-bold text-text-primary mt-0.5">{currentFuncObj.time_complexity || '—'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Space Complex.
                          </p>
                          <p className="text-sm font-bold text-text-primary mt-0.5">{currentFuncObj.space_complexity || '—'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Halstead Eff.
                          </p>
                          <p className="text-sm font-bold text-text-primary mt-0.5">{currentFuncObj.halstead_effort ? Math.round(currentFuncObj.halstead_effort) : '—'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/30 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest flex items-center">
                            Maintainability
                          </p>
                          <p className="text-sm font-bold text-text-primary mt-0.5">{currentFuncObj.maintainability_index ? Math.round(currentFuncObj.maintainability_index) : '—'}</p>
                        </div>
                      </div>

                      {currentFuncObj.fitness_score !== undefined && currentFuncObj.fitness_score !== null ? (
                        <div className="p-4 rounded-xl bg-accent-purple/5 border border-accent-purple/20">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-xs text-text-secondary flex items-center">
                              DNA Fitness Score
                              <InfoTooltip content="Current composite fitness evaluation based on speed, memory, edge-case coverage, and complexity. Higher is better." />
                            </span>
                            <span className="text-xs font-bold text-accent-purple">{currentFuncObj.fitness_score}</span>
                          </div>
                          <div className="w-full bg-bg-tertiary h-2 rounded-full overflow-hidden mt-1.5">
                            <div className="bg-accent-purple h-full rounded-full" style={{ width: `${Math.min(100, currentFuncObj.fitness_score)}%` }} />
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 rounded-xl bg-bg-primary/20 border border-border/20 text-center py-6">
                          <AlertCircle size={18} className="text-accent-yellow/60 mx-auto mb-2" />
                          <p className="text-xs text-text-secondary">No Performance DNA registered yet.</p>
                          <p className="text-[10px] text-text-secondary/50 mt-1">Run evolution to baseline this target.</p>
                        </div>
                      )}
                    </div>
                  ) : selectedFunc === 'ALL' ? (
                    <div className="h-48 flex flex-col items-center justify-center text-center text-text-secondary/60 border border-dashed border-accent-purple/40 bg-accent-purple/5 rounded-xl p-4">
                      <Cpu size={32} className="mb-2 text-accent-purple" />
                      <p className="text-sm font-bold text-accent-purple mb-1">Batch Evolution Mode</p>
                      <p className="text-xs text-text-secondary/80">All {functions.length} evolvable functions in this file will be evaluated sequentially.</p>
                    </div>
                  ) : (
                    <div className="h-48 flex flex-col items-center justify-center text-center text-text-secondary/40 border border-dashed border-border/40 rounded-xl">
                      <Cpu size={32} className="mb-2 opacity-20" />
                      <p className="text-xs">Select a function target to inspect its baseline DNA metrics.</p>
                    </div>
                  )}
                </div>

                {currentFuncObj && currentFuncObj.frozen && (
                  <div className="mt-4 p-3 rounded-xl border border-accent-red/20 bg-accent-red/5 flex items-start gap-2.5">
                    <Lock size={15} className="text-accent-red flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-bold text-accent-red">Target is Frozen</p>
                      <p className="text-[10px] text-text-secondary/80 mt-0.5">This function is locked in Code Manager. Go to Code Manager page to unfreeze it before starting evolution.</p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* STEP 2: CONFIGURATION */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="flex-1 rounded-2xl border border-border bg-white shadow-sm p-6 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <button onClick={() => setStep(1)} className="p-1 rounded-lg hover:bg-bg-tertiary text-text-secondary hover:text-text-primary transition-colors">
                    <ArrowLeft size={16} />
                  </button>
                  <h3 className="text-lg font-bold font-display text-text-primary">Step 2: Configure Mutation Settings</h3>
                </div>
                <p className="text-text-secondary text-xs mb-6 pl-7">
                  Configure how HezGene will mutate your function to find optimizations. 
                  You can enable Abstract Syntax Tree transformations, LLM-driven generative mutations, or both.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-7">
                  {/* Mutation Strategies */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">Engine Settings</h4>

                    {/* AST Mutations checkbox */}
                    <div className="flex items-start justify-between p-4 rounded-xl border border-border/40 bg-bg-tertiary/20">
                      <div className="flex-1 min-w-0 pr-4">
                        <p className="text-sm font-bold text-text-primary flex items-center">
                          AST Mutations
                          <InfoTooltip content="Applies 7 deterministic compiler rules (like combine operations, guard clauses, loop conversions) that are always syntax-safe and local." />
                        </p>
                        <p className="text-xs text-text-secondary mt-1">Deterministic refactoring rules</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={useAST}
                        onChange={(e) => setUseAST(e.target.checked)}
                        className="w-5 h-5 accent-accent-purple rounded cursor-pointer mt-1"
                      />
                    </div>

                    {/* LLM Mutations checkbox */}
                    <div className="flex items-start justify-between p-4 rounded-xl border border-border/40 bg-bg-tertiary/20">
                      <div className="flex-1 min-w-0 pr-4">
                        <p className="text-sm font-bold text-text-primary flex items-center">
                          LLM Mutations
                          <InfoTooltip content="Sends the code to your configured LLM (OpenAI, Ollama, Gemini, etc.) to perform semantic refactoring and algorithm optimizations." />
                        </p>
                        <p className="text-xs text-text-secondary mt-1">Generative AI algorithmic updates</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={useLLM}
                        onChange={(e) => setUseLLM(e.target.checked)}
                        className="w-5 h-5 accent-accent-purple rounded cursor-pointer mt-1"
                      />
                    </div>
                  </div>

                  {/* Safety & Generations Settings */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">Safety & Arena Scope</h4>

                    {/* Generations Selector */}
                    <div className="p-4 rounded-xl border border-border/40 bg-bg-tertiary/20">
                      <label className="block text-sm font-bold text-text-primary mb-2">
                        Generations (Mutant count)
                        <InfoTooltip content="The number of candidate mutant versions to generate and test. More generations increase search coverage but take longer." />
                      </label>
                      <select
                        className="w-full bg-bg-tertiary border border-border/60 rounded-lg p-2.5 text-xs text-text-primary focus:outline-none focus:border-accent-purple/60"
                        value={generations}
                        onChange={(e) => setGenerations(Number(e.target.value))}
                      >
                        {[3, 5, 8, 10].map((num) => (
                          <option key={num} value={num}>{num} Mutant Candidates</option>
                        ))}
                      </select>
                    </div>

                    {/* Auto-Deploy toggle */}
                    <div className="flex items-start justify-between p-4 rounded-xl border border-border/40 bg-bg-tertiary/20">
                      <div className="flex-1 min-w-0 pr-4">
                        <p className="text-sm font-bold text-text-primary flex items-center">
                          Auto-Deploy Winner
                          <InfoTooltip content="Surgically overwrite the source file with the winning mutant immediately after evolution finishes, provided the mutant beats the baseline performance." />
                        </p>
                        <p className="text-xs text-text-secondary mt-1">Deploy automatically upon improvement</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={applyMode}
                        onChange={(e) => setApplyMode(e.target.checked)}
                        className="w-5 h-5 accent-accent-green rounded cursor-pointer mt-1"
                      />
                    </div>
                  </div>
                </div>

                {!useAST && !useLLM && (
                  <div className="mt-4 mx-7 p-3 rounded-xl border border-accent-red/20 bg-accent-red/5 flex items-center gap-2 text-accent-red text-xs">
                    <AlertCircle size={14} />
                    <span>Please enable at least one mutation strategy (AST or LLM) to proceed.</span>
                  </div>
                )}
              </div>

              <div className="mt-8 pt-4 border-t border-border/20 flex justify-between">
                <button
                  onClick={() => setStep(1)}
                  className="px-5 py-2.5 rounded-xl border border-border/60 text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/30 text-sm font-semibold transition-colors"
                >
                  Back
                </button>
                
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={(!useAST && !useLLM) || (currentFuncObj && currentFuncObj.frozen)}
                  onClick={handleStart}
                  className={`px-6 py-3 rounded-xl font-bold text-sm flex items-center gap-2 transition-all ${
                    (!useAST && !useLLM) || (currentFuncObj && currentFuncObj.frozen)
                      ? 'bg-bg-tertiary text-text-secondary/40 border border-border/30 cursor-not-allowed'
                      : 'bg-accent-purple text-white shadow-lg shadow-accent-purple/25 hover:shadow-accent-purple/40 hover:bg-accent-purple/95'
                  }`}
                >
                  <Play size={15} /> Begin Genetic Evolution
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* STEP 3: LIVE COMBAT ARENA */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="flex-1 flex flex-col gap-6"
            >
              {/* Top Summary Card */}
              <div className="rounded-xl border border-border bg-white shadow-sm p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-text-primary flex items-center gap-1.5">
                    <Swords size={14} className="text-accent-yellow animate-pulse-glow" /> 
                    Live Arena Target: <span className="text-accent-purple font-mono">
                      {selectedFunc === 'ALL' ? (
                        <>
                          Batch Mode 
                          <span className="text-text-secondary text-xs ml-2 font-sans font-semibold">
                            (Processing {evo.messages.length > 0 ? (() => {
                              const currentFunc = [...evo.messages].reverse().find(m => m.function)?.function;
                              const idx = functions.findIndex((f: any) => f.qualified_name === currentFunc || f.name === currentFunc);
                              return idx >= 0 ? `${idx + 1} of ${functions.length}` : `...`;
                            })() : '...'})
                          </span>
                        </>
                      ) : (
                        selectedFunc
                      )}
                    </span>
                  </h3>
                  <p className="text-text-secondary text-[11px] mt-1">
                    Evaluating generated mutants in the 5 Correctness and Performance Rings.
                  </p>
                </div>
                
                {/* Micro Stage indicator */}
                <div className="flex items-center gap-2 bg-bg-tertiary/40 border border-border/40 p-2 rounded-lg text-xs">
                  <Activity size={12} className="animate-spin text-accent-cyan" />
                  <span className="text-text-secondary">Current Stage:</span>
                  <strong className="text-text-primary uppercase font-mono tracking-wider">{evo.stage?.replace(/_/g, ' ') || 'initializing'}</strong>
                </div>
              </div>

              {/* Live Columns */}
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-5 min-h-[350px]">
                {/* Left Column: Mutants Grid */}
                <div className="lg:col-span-1 rounded-xl border border-border bg-white shadow-sm flex flex-col overflow-hidden">
                  <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-bg-tertiary/50">
                    <span className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
                      <Bug size={14} className="text-accent-green" /> Spawned Mutants
                    </span>
                    <span className="bg-bg-tertiary px-2 py-0.5 rounded text-[10px] font-bold text-accent-green">{evo.mutants.length}</span>
                  </div>
                  
                  <div className="flex-1 p-3 space-y-3 overflow-y-auto max-h-[480px]">
                    <AnimatePresence>
                      {evo.mutants.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-text-secondary/30 py-12">
                          <Cpu size={32} className="mb-2 opacity-10 animate-pulse-glow" />
                          <p className="text-xs">Initializing mutation engines...</p>
                        </div>
                      ) : (
                        evo.mutants.map((m) => (
                          <MutantCard key={m.id} mutant={m} isWinner={m.strategy === winnerStrategy && !!evo.winner} />
                        ))
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                {/* Right Column: Logs and Rankings */}
                <div className="lg:col-span-2 flex flex-col gap-5 min-h-0">
                  {/* Rankings table if populated */}
                  {evo.rankings.length > 0 && (
                    <div className="rounded-xl border border-border bg-white shadow-sm overflow-hidden">
                      <div className="px-4 py-3 border-b border-border flex items-center gap-1.5 bg-bg-tertiary/50">
                        <Shield size={14} className="text-accent-yellow" />
                        <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">Arena Leaderboard</span>
                      </div>
                      <div className="overflow-x-auto max-h-48 overflow-y-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="text-[10px] text-text-secondary uppercase tracking-wider bg-bg-tertiary/40 sticky top-0">
                            <tr>
                              <th className="px-4 py-2">#</th>
                              <th className="px-4 py-2">Strategy</th>
                              <th className="px-4 py-2">Score</th>
                              <th className="px-4 py-2">Speed</th>
                              <th className="px-4 py-2">Memory</th>
                              <th className="px-4 py-2">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border/20">
                            {evo.rankings.map((r: any, i: number) => {
                              const meta = STRATEGY_LABELS[r.strategy] || (r.strategy.includes('llm') ? STRATEGY_LABELS['llm'] : STRATEGY_LABELS['unknown']);
                              const StrategyIcon = meta.icon;
                              return (
                                <tr key={r.mutant_id} className={`transition-colors ${i === 0 && r.passed ? 'bg-accent-green/5' : 'hover:bg-bg-tertiary/10'}`}>
                                  <td className="px-4 py-2 font-bold text-text-secondary">{r.rank}</td>
                                  <td className="px-4 py-2 font-medium">
                                    <div className="flex items-center gap-2">
                                      <StrategyIcon size={13} className={meta.color} />
                                      <span className="font-bold text-text-primary">{meta.label || r.strategy}</span>
                                    </div>
                                  </td>
                                  <td className={`px-4 py-2 font-bold ${r.score > 50 ? 'text-accent-green' : 'text-accent-yellow'}`}>{r.score?.toFixed(1)}</td>
                                  <td className="px-4 py-2 font-mono">{r.speed_ms?.toFixed(3)}ms</td>
                                  <td className="px-4 py-2 font-mono">{r.memory_bytes}B</td>
                                  <td className="px-4 py-2">
                                    {r.passed ? (
                                      <span className="text-accent-green text-[10px] font-bold flex items-center gap-1"><CheckCircle2 size={10} />PASSED</span>
                                    ) : (
                                      <span className="text-accent-red text-[10px] font-bold flex items-center gap-1"><XCircle size={10} />FAILED</span>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Realtime Live log feed */}
                  <div className="flex-1 rounded-xl border border-border bg-white shadow-sm overflow-hidden flex flex-col min-h-[160px]">
                    <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-bg-tertiary/50">
                      <span className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
                        <Activity size={14} className="text-accent-cyan" /> Pipeline Live Stream
                      </span>
                    </div>
                    <div ref={logRef} className="flex-1 p-4 overflow-y-auto font-mono text-[11px] space-y-2 bg-bg-tertiary max-h-64">
                      {evo.messages.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-text-secondary/30">
                          <p>Waiting for connection...</p>
                        </div>
                      ) : (
                        evo.messages.map((msg, i) => (
                          <motion.div key={i} initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }}
                            className="flex gap-2 text-text-secondary/80">
                            <span className="text-accent-cyan/60 flex-shrink-0">[{new Date().toLocaleTimeString()}]</span>
                            <span className="uppercase text-[9px] font-bold tracking-wider text-text-secondary/50 w-24 flex-shrink-0 truncate">
                              {msg.stage?.replace(/_/g, ' ')}
                            </span>
                            <span className="text-text-primary/75 flex items-center flex-wrap gap-1.5">
                              {msg.message || msg.warning || ''}
                              {msg.mutant && (
                                <>Spawned mutant: <MutantBadge strategy={msg.mutant.strategy} /></>
                              )}
                              {msg.mutant_result && (
                                <>Gauntlet Result: <MutantBadge strategy={msg.mutant_result.strategy} /> {msg.mutant_result.passed ? <span className="text-accent-green font-bold text-[9px] uppercase tracking-wider bg-accent-green/10 px-1 py-0.5 rounded">Passed</span> : <span className="text-accent-red font-bold text-[9px] uppercase tracking-wider bg-accent-red/10 px-1 py-0.5 rounded">Failed</span>}</>
                              )}
                            </span>
                          </motion.div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* STEP 4: PROMOTION & RESULTS */}
          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="flex-1 flex flex-col gap-6"
            >
              {selectedFunc === 'ALL' ? (
                <div className="rounded-2xl border border-accent-purple/30 bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-bold font-display text-text-primary flex items-center gap-2 mb-4">
                    <Trophy className="text-accent-purple" /> Batch Evolution Complete
                  </h3>
                  <p className="text-xs text-text-secondary mb-6">
                    Processed {evo.finalResults?.length || 0} functions. Below is the summary of improvements.
                  </p>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                    {evo.finalResults?.map((r: any, i: number) => {
                      const status = deployingBatch[r.function];
                      return (
                        <div key={i} className={`p-4 rounded-xl border ${r.status === 'evolved' ? 'border-accent-green/40 bg-accent-green/5' : 'border-border/50 bg-bg-tertiary/30'} flex items-center justify-between`}>
                          <div className="flex flex-col">
                            <span className="font-mono text-sm font-bold text-text-primary">{r.function}</span>
                            <span className="text-[11px] text-text-secondary mt-1">
                              {r.status === 'evolved' ? 'Evolution Successful (Improved)' : r.reason || 'No improvement found'}
                            </span>
                          </div>
                          {r.status === 'evolved' && (
                            <div className="flex items-center gap-3">
                              <span className="text-[10px] font-bold text-accent-green uppercase tracking-wider bg-accent-green/10 px-2 py-1 rounded hidden sm:inline-block">Evolved</span>
                              
                              {status === 'success' || applyMode ? (
                                <span className="text-accent-green font-bold text-[10px] flex items-center gap-1 bg-accent-green/10 px-2 py-1 rounded">
                                  <CheckCircle2 size={12} /> Deployed
                                </span>
                              ) : status === 'error' ? (
                                <span className="text-accent-red font-bold text-[10px] flex items-center gap-1 bg-accent-red/10 px-2 py-1 rounded">
                                  <XCircle size={12} /> Error
                                </span>
                              ) : (
                                <button
                                  type="button"
                                  disabled={status === 'loading'}
                                  onClick={() => handleBatchDeploy(r.function)}
                                  className="px-3 py-1.5 bg-accent-green hover:bg-accent-green/90 text-white font-bold text-[10px] rounded flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
                                >
                                  {status === 'loading' ? <RefreshCw size={12} className="animate-spin" /> : <Rocket size={12} />}
                                  Deploy
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <>
                  {/* Winner Announcement Details */}
              {evo.winner ? (
                <div className="rounded-2xl border border-accent-yellow/45 bg-gradient-to-br from-accent-yellow/5 via-accent-purple/5 to-white p-6 relative overflow-hidden shadow-sm">
                  <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Trophy size={140} className="text-accent-yellow" />
                  </div>
                  
                  <div className="flex flex-col md:flex-row items-center md:items-start gap-5">
                    <div className="w-14 h-14 rounded-full bg-accent-yellow/10 flex items-center justify-center text-accent-yellow border border-accent-yellow/20 flex-shrink-0">
                      <Trophy size={28} className="animate-trophy" />
                    </div>
                    
                    <div className="flex-1 text-center md:text-left">
                      <span className="text-[10px] bg-accent-yellow/10 border border-accent-yellow/25 px-2 py-0.5 rounded text-accent-yellow font-bold uppercase tracking-wider">Winning Mutant Selected</span>
                      <h3 className="text-lg font-bold font-display text-text-primary mt-2">Evolution Successful!</h3>
                      <p className="text-xs text-text-secondary mt-1">
                        HezGene successfully generated a mutant that satisfies all correctness criteria and outperforms the baseline function.
                      </p>

                      {/* Performance Delta Board */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                        <div className="p-3 rounded-xl bg-bg-primary/40 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest">Fitness Gain</p>
                          <p className="text-lg font-extrabold text-accent-green mt-1">{evo.winner.improvement}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/40 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest">Speed Change</p>
                          <p className="text-sm font-bold text-text-primary mt-1.5 font-mono">
                            {evo.winner.speed_before?.toFixed(4)}ms → {evo.winner.speed_after?.toFixed(4)}ms
                          </p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/40 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest">Memory Delta</p>
                          <p className="text-sm font-bold text-text-primary mt-1.5 font-mono">
                            {evo.winner.memory_before}B → {evo.winner.memory_after}B
                          </p>
                        </div>
                        <div className="p-3 rounded-xl bg-bg-primary/40 border border-border/20">
                          <p className="text-[10px] text-text-secondary uppercase tracking-widest">Strategy Used</p>
                          <p className="text-xs font-bold text-accent-cyan mt-2">
                            {STRATEGY_LABELS[evo.winner.strategy]?.emoji} {STRATEGY_LABELS[evo.winner.strategy]?.label || evo.winner.strategy}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Manual Promotion Control */}
                  {!applyMode && !deploySuccess && (
                    <div className="mt-6 pt-5 border-t border-border/25 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <p className="text-xs font-bold text-text-primary">Manual Promotion Required</p>
                        <p className="text-[10px] text-text-secondary">Auto-deploy was off. Click below to surgically write this winner back into your source code.</p>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        disabled={isDeploying}
                        onClick={handleManualDeploy}
                        className="px-6 py-2.5 bg-accent-green hover:bg-accent-green/90 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-lg shadow-accent-green/20"
                      >
                        {isDeploying ? <RefreshCw size={13} className="animate-spin" /> : <Rocket size={13} />}
                        Deploy Evolved Code
                        <InfoTooltip content="This replaces the function source block in your python file with the optimized mutant version. A backup is created automatically." />
                      </motion.button>
                    </div>
                  )}

                  {/* Deploy Status Messages */}
                  {deploySuccess && (
                    <div className="mt-4 p-3 bg-accent-green/10 border border-accent-green/30 rounded-xl flex items-center gap-2 text-accent-green text-xs font-bold">
                      <CheckCircle2 size={15} />
                      <span>Code deployed successfully! Function replaced in workspace and backup created in .hezgene/backups.</span>
                    </div>
                  )}

                  {deployError && (
                    <div className="mt-4 p-3 bg-accent-red/10 border border-accent-red/30 rounded-xl flex items-center gap-2 text-accent-red text-xs font-bold">
                      <XCircle size={15} />
                      <span>Deployment Failed: {deployError}</span>
                    </div>
                  )}

                  {applyMode && (
                    <div className="mt-4 p-3 bg-accent-green/15 border border-accent-green/20 rounded-xl flex items-center gap-2 text-accent-green text-xs font-bold">
                      <CheckCircle2 size={15} />
                      <span>Auto-Deploy was enabled. Winner has been successfully written to the source code file.</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-2xl border border-border/50 bg-bg-secondary/40 p-12 text-center">
                  <AlertCircle size={40} className="text-accent-yellow mx-auto mb-3" />
                  <h3 className="text-lg font-bold font-display text-text-primary">No Fitness Improvements Found</h3>
                  <p className="text-text-secondary text-xs mt-1.5 max-w-md mx-auto">
                    The gauntlet run completed, but no generated mutants surpassed the fitness of the original baseline code. 
                    Your original code remains active and unchanged.
                  </p>
                </div>
              )}

              {/* Code Diff section */}
              {evo.winner && (
                <div className="rounded-xl border border-border/50 bg-bg-secondary/30 overflow-hidden">
                  <div className="px-4 py-3 border-b border-border/30 flex items-center justify-between bg-bg-tertiary/10">
                    <span className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
                      <Eye size={14} className="text-accent-purple" /> Code Comparison
                    </span>
                    <button
                      onClick={() => setShowCode(!showCode)}
                      className="text-[10px] font-bold text-accent-purple hover:underline"
                    >
                      {showCode ? 'Collapse' : 'Expand'}
                    </button>
                  </div>
                  
                  <AnimatePresence>
                    {showCode && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 overflow-hidden"
                      >
                        <div className="flex flex-col min-h-0">
                          <p className="text-xs font-bold text-accent-red mb-1.5 uppercase tracking-wider pl-1">Original Code</p>
                          <pre className="text-[11px] bg-bg-primary/80 border border-border/40 rounded-xl p-3.5 overflow-auto max-h-64 font-mono text-text-secondary/90 leading-relaxed">{evo.originalSource}</pre>
                        </div>
                        <div className="flex flex-col min-h-0">
                          <p className="text-xs font-bold text-accent-green mb-1.5 uppercase tracking-wider pl-1">Optimized Winner</p>
                          <pre className="text-[11px] bg-bg-primary/80 border border-border/40 rounded-xl p-3.5 overflow-auto max-h-64 font-mono text-accent-green/90 leading-relaxed">{evo.winner.evolved_source}</pre>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
                </>
              )}

              {/* Reset Control */}
              <div className="flex justify-end pt-4 border-t border-border/20">
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-bg-tertiary hover:bg-bg-tertiary/80 text-white font-bold text-sm rounded-xl transition-all flex items-center gap-1.5"
                >
                  Start New Evolution Session
                  <InfoTooltip content="Reset the evolution state, clear the session caches, and go back to Step 1 selection." />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error Banner */}
      <AnimatePresence>
        {evo.error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 p-4 rounded-xl border border-accent-red/30 bg-accent-red/5 text-accent-red text-xs flex items-center gap-2"
          >
            <AlertCircle size={15} />
            <span><strong>Pipeline Error:</strong> {evo.error}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
