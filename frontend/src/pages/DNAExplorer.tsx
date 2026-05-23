import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dna, Cpu, Zap, BookOpen, Search, ChevronDown, ChevronUp, Shield, Bug,
} from 'lucide-react';
import { getFunctions } from '../api';

function FitnessBar({ value, max = 100, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full h-1.5 rounded-full bg-bg-tertiary/60 overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className={`h-full rounded-full ${color}`}
      />
    </div>
  );
}

function DNAProfile({ dna }: { dna: any }) {
  const genes = [
    { label: 'Performance', desc: 'Execution speed', value: Math.max(0, 100 - (dna.avg_execution_time_ms || 0)), icon: Zap, color: 'bg-accent-yellow', weight: '30%' },
    { label: 'Reliability', desc: 'Bug count penalty', value: Math.max(0, 100 - (dna.bug_count || 0) * 10), icon: Shield, color: 'bg-accent-green', weight: '30%' },
    { label: 'Readability', desc: 'Code clarity', value: (dna.readability_score || 0) * 100, icon: BookOpen, color: 'bg-accent-cyan', weight: '20%' },
    { label: 'Coverage', desc: 'Test coverage', value: (dna.test_coverage || 0) * 100, icon: Bug, color: 'bg-accent-purple', weight: '15%' },
    { label: 'Simplicity', desc: 'Low complexity', value: Math.max(0, 100 - (dna.cyclomatic_complexity || 0) * 10), icon: Cpu, color: 'bg-accent-pink', weight: '5%' },
  ];

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      className="overflow-hidden"
    >
      <div className="pt-4 pb-2 px-1 space-y-3">
        {genes.map((g) => (
          <div key={g.label} className="flex items-center gap-3">
            <g.icon size={13} className="text-text-secondary flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center mb-0.5">
                <span className="text-xs font-medium">{g.label}</span>
                <span className="text-[10px] text-text-secondary">{g.value.toFixed(0)}% <span className="opacity-50">({g.weight})</span></span>
              </div>
              <FitnessBar value={g.value} color={g.color} />
            </div>
          </div>
        ))}

        <div className="mt-3 pt-3 border-t border-border/30 grid grid-cols-3 gap-y-3 gap-x-2 text-xs">
          <div className="text-center">
            <p className="text-text-secondary">LOC</p>
            <p className="font-bold font-mono">{dna.lines_of_code || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-text-secondary">Time</p>
            <p className="font-bold font-mono text-accent-purple">{dna.time_complexity || '—'}</p>
          </div>
          <div className="text-center">
            <p className="text-text-secondary">Space</p>
            <p className="font-bold font-mono text-accent-cyan">{dna.space_complexity || '—'}</p>
          </div>
          <div className="text-center">
            <p className="text-text-secondary">Halstead</p>
            <p className="font-bold font-mono">{dna.halstead_effort ? Math.round(dna.halstead_effort) : '—'}</p>
          </div>
          <div className="text-center">
            <p className="text-text-secondary">Maint. Idx</p>
            <p className="font-bold font-mono">{dna.maintainability_index ? Math.round(dna.maintainability_index) : '—'}</p>
          </div>
          <div className="text-center">
            <p className="text-text-secondary">Cyclomatic</p>
            <p className="font-bold font-mono">{dna.cyclomatic_complexity || 0}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function DNAExplorer() {
  const [dnaList, setDnaList] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'fitness' | 'name' | 'complexity'>('fitness');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getFunctions()
      .then((res) => res.data && setDnaList(res.data))
      .catch(() => {});
  }, []);

  const toggleSort = (key: typeof sortBy) => {
    if (sortBy === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    else { setSortBy(key); setSortDir('desc'); }
  };

  const filtered = dnaList
    .filter((d) => {
      if (!search) return true;
      const s = search.toLowerCase();
      return d.name?.toLowerCase().includes(s) || d.module?.toLowerCase().includes(s) || d.qualified_name?.toLowerCase().includes(s);
    })
    .sort((a, b) => {
      let va: any, vb: any;
      if (sortBy === 'fitness') { va = a.fitness_score || 0; vb = b.fitness_score || 0; }
      else if (sortBy === 'name') { va = a.name || ''; vb = b.name || ''; }
      else { va = a.cyclomatic_complexity || 0; vb = b.cyclomatic_complexity || 0; }
      if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortDir === 'asc' ? va - vb : vb - va;
    });

  const fitnessColor = (score: number) => {
    if (score >= 70) return 'text-accent-green';
    if (score >= 40) return 'text-accent-yellow';
    return 'text-accent-red';
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <header className="mb-5">
        <h2 className="text-2xl font-extrabold font-display gradient-purple-pink">DNA Explorer</h2>
        <p className="text-text-secondary text-sm mt-0.5">Analyze the genetic makeup of your codebase</p>
      </header>

      {/* Search & Sort */}
      <div className="flex gap-3 mb-5">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary/50" />
          <input
            type="text" placeholder="Search functions..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bg-secondary/50 border border-border/40 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-accent-purple/50"
          />
        </div>
        <div className="flex gap-1 bg-bg-secondary/50 border border-border/40 rounded-lg p-1">
          {[
            { key: 'fitness' as const, label: 'Fitness' },
            { key: 'name' as const, label: 'Name' },
            { key: 'complexity' as const, label: 'Complexity' },
          ].map((s) => (
            <button key={s.key} onClick={() => toggleSort(s.key)}
              className={`px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1 transition-all ${
                sortBy === s.key ? 'bg-accent-purple/15 text-accent-purple' : 'text-text-secondary hover:text-text-primary'
              }`}>
              {s.label}
              {sortBy === s.key && (sortDir === 'desc' ? <ChevronDown size={11} /> : <ChevronUp size={11} />)}
            </button>
          ))}
        </div>
      </div>

      {/* Function Table */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {filtered.length === 0 ? (
          <div className="rounded-xl border border-border/50 bg-bg-secondary/30 p-12 text-center text-text-secondary">
            <Dna size={40} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">{dnaList.length === 0 ? 'No DNA tracked yet' : 'No matches found'}</p>
            <p className="text-xs mt-1">Upload and scan files to populate the DNA registry</p>
          </div>
        ) : (
          filtered.map((dna, i) => (
            <motion.div
              key={dna.qualified_name || i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="rounded-xl border border-border/50 bg-bg-secondary/40 backdrop-blur-sm overflow-hidden"
            >
              <div
                className="flex items-center gap-4 px-5 py-3.5 cursor-pointer hover:bg-bg-tertiary/20 transition-colors"
                onClick={() => setExpanded(expanded === dna.qualified_name ? null : dna.qualified_name)}
              >
                <Dna size={16} className="text-accent-purple flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold font-mono truncate">{dna.name}</p>
                  <p className="text-xs text-text-secondary truncate">{dna.module}</p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="text-center hidden sm:block">
                    <p className="text-text-secondary/60">Fitness</p>
                    <p className={`font-bold text-sm ${fitnessColor(dna.fitness_score || 0)}`}>{dna.fitness_score?.toFixed(1) || '—'}</p>
                  </div>
                  <div className="text-center hidden md:block">
                    <p className="text-text-secondary/60">Speed</p>
                    <p className="font-mono font-medium">{dna.avg_execution_time_ms?.toFixed(2) || '—'}ms</p>
                  </div>
                  <div className="text-center hidden md:block">
                    <p className="text-text-secondary/60">LOC</p>
                    <p className="font-mono font-medium">{dna.lines_of_code || '—'}</p>
                  </div>
                  <div className="text-center hidden lg:block">
                    <p className="text-text-secondary/60">Evols</p>
                    <p className="font-mono font-medium text-accent-purple">{dna.evolution_count || 0}</p>
                  </div>
                  {expanded === dna.qualified_name ? <ChevronUp size={14} className="text-text-secondary" /> : <ChevronDown size={14} className="text-text-secondary" />}
                </div>
              </div>

              <AnimatePresence>
                {expanded === dna.qualified_name && (
                  <div className="border-t border-border/30 px-5 pb-4">
                    <DNAProfile dna={dna} />
                  </div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
