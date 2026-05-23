import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, Trophy, Dna, Snowflake, TrendingUp, Trash2 } from 'lucide-react';
import { getHistory, clearHistory, deleteHistoryItem } from '../api';

export default function History() {
  const [entries, setEntries] = useState<any[]>([]);
  const [filter, setFilter] = useState<'all' | 'evolved' | 'frozen'>('all');

  const loadHistory = () => {
    getHistory(100, filter === 'all' ? undefined : filter)
      .then((res) => res.data && setEntries(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    loadHistory();
  }, [filter]);

  const formatDate = (ts: number) => {
    if (!ts) return '—';
    return new Date(ts * 1000).toLocaleString();
  };

  const handleClearHistory = async () => {
    if (window.confirm('Wipe the entire evolution registry and history log?')) {
      try {
        await clearHistory();
        setEntries([]);
      } catch (err: any) {
        alert(err.message || 'Failed to clear history.');
      }
    }
  };

  const handleDeleteItem = async (target: string) => {
    if (window.confirm(`Remove "${target}" from DNA tracking?`)) {
      try {
        await deleteHistoryItem(target);
        loadHistory();
      } catch (err: any) {
        alert(err.message || 'Failed to delete history item.');
      }
    }
  };

  return (
    <div className="p-6 h-full flex flex-col">
      <header className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold font-display">Battle History</h2>
          <p className="text-text-secondary text-sm mt-0.5">Track all past evolutions and optimizations</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-bg-secondary/50 border border-border/40 rounded-lg p-1">
            {(['all', 'evolved', 'frozen'] as const).map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  filter === f ? 'bg-accent-purple/15 text-accent-purple' : 'text-text-secondary hover:text-text-primary'
                }`}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <button
            onClick={handleClearHistory}
            className="px-3 py-1.5 rounded-lg border border-accent-red/30 bg-accent-red/10 text-accent-red hover:bg-accent-red/20 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            Clear History
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        {entries.length === 0 ? (
          <div className="rounded-xl border border-border/50 bg-bg-secondary/30 p-12 text-center text-text-secondary">
            <Clock size={40} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">No evolution history yet</p>
            <p className="text-xs mt-1">Run an evolution to see results here</p>
          </div>
        ) : (
          <div className="rounded-xl border border-border/50 bg-bg-secondary/40 backdrop-blur-sm overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-text-secondary uppercase tracking-wider bg-bg-tertiary/30 border-b border-border/30">
                <tr>
                  <th className="px-5 py-3">Target</th>
                  <th className="px-5 py-3">Fitness</th>
                  <th className="px-5 py-3">Evolutions</th>
                  <th className="px-5 py-3">Last Evolved</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {entries.map((e: any, i: number) => (
                  <motion.tr
                     key={e.target}
                     initial={{ opacity: 0, x: -5 }}
                     animate={{ opacity: 1, x: 0 }}
                     transition={{ delay: i * 0.03 }}
                     className="hover:bg-bg-tertiary/20 transition-colors"
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <Dna size={14} className="text-accent-purple flex-shrink-0" />
                        <span className="font-mono text-xs truncate max-w-[200px]">{e.target}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`font-bold ${(e.fitness || 0) >= 60 ? 'text-accent-green' : (e.fitness || 0) >= 30 ? 'text-accent-yellow' : 'text-accent-red'}`}>
                        {e.fitness?.toFixed(1) ?? '—'}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        {e.evolutions > 0 ? (
                          <>
                            <TrendingUp size={13} className="text-accent-green" />
                            <span className="font-bold text-accent-green">{e.evolutions}</span>
                          </>
                        ) : (
                          <span className="text-text-secondary">0</span>
                        )}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-xs text-text-secondary font-mono">{formatDate(e.last_evolved)}</td>
                    <td className="px-5 py-3">
                      {e.frozen ? (
                        <span className="flex items-center gap-1 text-accent-cyan text-xs font-bold">
                          <Snowflake size={12} /> Frozen
                        </span>
                      ) : e.evolutions > 0 ? (
                        <span className="flex items-center gap-1 text-accent-green text-xs font-bold">
                          <Trophy size={12} /> Evolved
                        </span>
                      ) : (
                        <span className="text-text-secondary text-xs">Tracked</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleDeleteItem(e.target)}
                        className="p-1.5 rounded-lg text-text-secondary hover:text-accent-red hover:bg-accent-red/10 transition-colors"
                        title="Delete entry"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

