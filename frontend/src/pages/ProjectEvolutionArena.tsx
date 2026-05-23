import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Play, Pause, Square, Zap, FileCode, CheckCircle2,
  XCircle, Loader2, Sparkles, AlertCircle, RefreshCw, Trophy
} from 'lucide-react';
import { useProjectEvolution } from '../hooks/useProjectEvolution';

export default function ProjectEvolutionArena({ target }: { target: string }) {
  const [searchParams] = useSearchParams();
  const [useLLM, setUseLLM] = useState(false);
  const [applyMode, setApplyMode] = useState(false);
  const [generations, setGenerations] = useState(5);
  
  const evo = useProjectEvolution();
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [evo.messages]);

  const handleStart = () => {
    evo.start({
      project_path: target === '.' ? '.' : undefined,
      file_path: target !== '.' ? target : undefined,
      use_llm: useLLM,
      apply: applyMode,
      generations: generations,
    });
  };

  const percentComplete = evo.totalFunctions > 0 ? (evo.completedFunctions / evo.totalFunctions) * 100 : 0;

  return (
    <div className="p-6 min-h-screen flex flex-col max-w-6xl mx-auto w-full">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold font-display gradient-yellow-red">Project Evolution</h2>
          <p className="text-text-secondary text-sm mt-0.5">Automated genetic refactoring across multiple files</p>
        </div>
        {evo.isRunning && !evo.isPaused && (
          <div className="flex items-center gap-2 bg-accent-green/10 border border-accent-green/30 px-3 py-1 rounded-full text-accent-green text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-green opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-green" />
            </span>
            EVOLVING PROJECT
          </div>
        )}
        {evo.isPaused && (
          <div className="flex items-center gap-2 bg-accent-yellow/10 border border-accent-yellow/30 px-3 py-1 rounded-full text-accent-yellow text-xs font-semibold">
            PAUSED
          </div>
        )}
      </header>

      {!evo.isRunning && evo.stage === '' ? (
        <div className="rounded-xl border border-border bg-bg-secondary p-6 shadow-sm">
          <h3 className="font-bold mb-4">Project Evolution Settings</h3>
          <p className="text-sm text-text-secondary mb-6">You are about to evolve {target === '.' ? 'the entire project' : `all functions in ${target}`}.</p>
          
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 border rounded-xl bg-bg-primary">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm flex items-center gap-2"><Sparkles size={16} className="text-accent-cyan"/> LLM Mutations</span>
                <input type="checkbox" className="toggle toggle-primary" checked={useLLM} onChange={(e) => setUseLLM(e.target.checked)} />
              </div>
              <p className="text-xs text-text-secondary">Use AI models to generate complex optimizations alongside AST mutations.</p>
            </div>

            <div className="p-4 border rounded-xl bg-bg-primary">
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-sm flex items-center gap-2"><Zap size={16} className="text-accent-purple"/> Apply Mode</span>
                <input type="checkbox" className="toggle toggle-primary" checked={applyMode} onChange={(e) => setApplyMode(e.target.checked)} />
              </div>
              <p className="text-xs text-text-secondary">If disabled, changes are saved to the sandbox. If enabled, original files will be modified.</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button onClick={handleStart} className="px-6 py-2 bg-accent-purple text-bg-primary rounded-lg font-bold flex items-center gap-2 hover:bg-accent-purple/90">
              <Play size={18} className="fill-current" /> Start Project Evolution
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-6 flex-1 min-h-0">
          <div className="col-span-2 flex flex-col gap-4">
            {/* Progress Card */}
            <div className="rounded-xl border border-border bg-bg-secondary p-5 shadow-sm shrink-0">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold flex items-center gap-2">
                  <Play size={18} className="text-accent-cyan" /> Progress
                </h3>
                <div className="text-sm font-bold">
                  {evo.completedFunctions} / {evo.totalFunctions} functions
                </div>
              </div>
              <div className="h-4 bg-bg-primary rounded-full overflow-hidden mb-4 border border-border/50">
                <motion.div 
                  className="h-full bg-gradient-to-r from-accent-cyan to-accent-purple"
                  initial={{ width: 0 }}
                  animate={{ width: `${percentComplete}%` }}
                />
              </div>
              
              <div className="flex items-center gap-2 mt-4">
                {evo.isRunning && !evo.isPaused && (
                  <button onClick={evo.pause} className="px-4 py-1.5 bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/30 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-accent-yellow/30">
                    <Pause size={14} className="fill-current" /> Pause
                  </button>
                )}
                {evo.isPaused && (
                  <button onClick={evo.resume} className="px-4 py-1.5 bg-accent-green/20 text-accent-green border border-accent-green/30 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-accent-green/30">
                    <Play size={14} className="fill-current" /> Resume
                  </button>
                )}
                {evo.isRunning && (
                  <button onClick={evo.cancel} className="px-4 py-1.5 bg-accent-red/20 text-accent-red border border-accent-red/30 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-accent-red/30">
                    <Square size={14} className="fill-current" /> Cancel
                  </button>
                )}
                {!evo.isRunning && evo.stage !== '' && (
                  <button onClick={evo.reset} className="px-4 py-1.5 bg-text-primary text-bg-primary rounded-lg text-sm font-bold flex items-center gap-2">
                    <RefreshCw size={14} /> Reset
                  </button>
                )}
              </div>
            </div>

            {/* Function Status List */}
            <div className="rounded-xl border border-border bg-bg-secondary p-5 shadow-sm flex-1 overflow-auto">
              <h3 className="font-bold mb-4">Evolution Status</h3>
              <div className="space-y-3">
                {Object.entries(evo.functionStatuses).map(([key, data]) => {
                  const [file, func] = key.split(':');
                  return (
                    <div key={key} className="p-3 bg-bg-primary border border-border/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-xs text-text-secondary">{file}</p>
                          <p className="text-sm font-mono font-bold">{func}</p>
                        </div>
                        <div>
                          {data.status === 'running' && <span className="text-accent-cyan flex items-center gap-1 text-xs font-bold"><Loader2 size={12} className="animate-spin" /> RUNNING</span>}
                          {data.status === 'extracting_dna' && <span className="text-text-secondary flex items-center gap-1 text-xs">Extracting...</span>}
                          {data.status === 'spawning_mutants' && <span className="text-accent-purple flex items-center gap-1 text-xs">Spawning...</span>}
                          {data.status === 'arena_fight' && <span className="text-accent-yellow flex items-center gap-1 text-xs animate-pulse">Fighting...</span>}
                          {data.status === 'evolved' && <span className="text-accent-green flex items-center gap-1 text-xs font-bold"><CheckCircle2 size={12} /> IMPROVED</span>}
                          {data.status === 'unchanged' && <span className="text-text-secondary flex items-center gap-1 text-xs"><CheckCircle2 size={12} /> UNCHANGED</span>}
                          {data.status === 'error' && <span className="text-accent-red flex items-center gap-1 text-xs"><AlertCircle size={12} /> ERROR</span>}
                        </div>
                      </div>
                      
                      {data.status === 'evolved' && data.improvements && (
                        <div className="text-xs bg-accent-green/10 text-accent-green p-2 rounded flex justify-between">
                          <span>Speed: {data.improvements.speed_after.toFixed(3)}ms</span>
                          <span className="font-bold">+{((data.improvements.fitness_after - data.improvements.fitness_before) / data.improvements.fitness_before * 100).toFixed(1)}%</span>
                        </div>
                      )}
                    </div>
                  );
                })}
                {Object.keys(evo.functionStatuses).length === 0 && (
                  <p className="text-sm text-text-secondary italic">Waiting to process functions...</p>
                )}
              </div>
            </div>
          </div>

          {/* Activity Log */}
          <div className="rounded-xl border border-border bg-bg-secondary flex flex-col shadow-sm overflow-hidden h-[calc(100vh-120px)] sticky top-6">
            <div className="bg-bg-tertiary border-b border-border p-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-2">
                <FileCode size={14} /> Live Terminal Log
              </h3>
            </div>
            <div ref={logRef} className="flex-1 overflow-auto p-4 space-y-2 bg-[#0d1117] font-mono text-[11px] leading-relaxed select-text">
              {evo.messages.length === 0 && <span className="text-[#8b949e]">Waiting for evolution to begin...</span>}
              {evo.messages.map((msg, i) => {
                let color = "text-[#c9d1d9]";
                if (msg.stage.includes("error")) color = "text-[#ff7b72]";
                if (msg.stage === "winner_selected" || msg.stage === "function_complete" && msg.status === "evolved") color = "text-[#3fb950] font-bold";
                if (msg.stage === "no_improvement" || msg.stage === "project_started") color = "text-[#d2a8ff]";
                
                let text = msg.message || `[${msg.stage}] ${msg.function || ''}`;
                if (msg.stage === "mutant_spawned") text = `[SPAWN] Generated mutant using ${msg.mutant?.strategy}`;
                if (msg.stage === "fight_result") text = `[FIGHT] Mutant ${msg.mutant_result?.strategy} ${msg.mutant_result?.passed ? 'survived' : 'died'}`;
                
                return (
                  <div key={i} className={`whitespace-pre-wrap word-break ${color}`}>
                    <span className="text-[#484f58] mr-2">
                      {new Date().toISOString().split('T')[1].slice(0, -1)}
                    </span>
                    {text}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
