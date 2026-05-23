import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Dna, Swords, Zap, Shield, TrendingUp, Upload, Activity,
  ArrowRight, Sparkles, Clock, Trophy, BookOpen
} from 'lucide-react';
import { getStats } from '../api';

interface Stats {
  total_functions: number;
  evolved_functions: number;
  frozen_functions: number;
  total_evolutions: number;
  avg_fitness: number;
  backups: number;
  recent_activity: any[];
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: 'easeOut' as const },
  }),
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    getStats()
      .then((res) => res.data && setStats(res.data))
      .catch(() => {});
  }, []);

  const statCards = [
    {
      title: 'Tracked Functions',
      value: stats?.total_functions ?? 0,
      icon: Dna,
      color: 'text-accent-cyan',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-cyan/30',
      iconBg: 'bg-accent-cyan/10',
    },
    {
      title: 'Total Evolutions',
      value: stats?.total_evolutions ?? 0,
      icon: Swords,
      color: 'text-accent-purple',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-purple/30',
      iconBg: 'bg-accent-purple/10',
    },
    {
      title: 'Avg Fitness',
      value: stats?.avg_fitness ? `${stats.avg_fitness.toFixed(1)}` : '—',
      icon: TrendingUp,
      color: 'text-accent-green',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-green/30',
      iconBg: 'bg-accent-green/10',
    },
    {
      title: 'Functions Evolved',
      value: stats?.evolved_functions ?? 0,
      icon: Sparkles,
      color: 'text-accent-yellow',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-yellow/30',
      iconBg: 'bg-accent-yellow/10',
    },
    {
      title: 'Frozen (Protected)',
      value: stats?.frozen_functions ?? 0,
      icon: Shield,
      color: 'text-accent-red',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-red/30',
      iconBg: 'bg-accent-red/10',
    },
    {
      title: 'Safety Backups',
      value: stats?.backups ?? 0,
      icon: Activity,
      color: 'text-accent-pink',
      bg: 'bg-secondary',
      border: 'border-border',
      glow: 'hover:shadow-md hover:border-accent-pink/30',
      iconBg: 'bg-accent-pink/10',
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="mb-10"
      >
        <div className="relative overflow-hidden rounded-3xl border-none bg-[#0a0a0a] text-white p-8 sm:p-10 shadow-lg">
          {/* Hostinger-style bright background blobs on the dark card */}
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-purple/30 rounded-full blur-[100px] -translate-y-1/3 translate-x-1/3" />
          <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-accent-pink/20 rounded-full blur-[90px] translate-y-1/2" />

          <div className="relative z-10 flex items-center justify-between">
            <div>
              <h1 className="text-4xl sm:text-5xl font-extrabold font-display tracking-tight mb-3">
                <span className="text-white">HezGene</span>{' '}
                <span className="text-white/90">Command Center</span>
              </h1>
              <p className="text-white/70 text-lg max-w-xl mb-8">
                The world's first autonomous genetic software evolution platform.
                Code that writes, optimizes, and heals itself.
              </p>

              <div className="flex gap-4">
                <Link to="/files">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-white text-black rounded-xl font-bold text-sm shadow-md hover:bg-gray-100 transition-colors"
                  >
                    <Upload size={18} /> Upload Code
                  </motion.button>
                </Link>
                <Link to="/arena">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center justify-center gap-2 px-6 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl text-white font-bold text-sm hover:bg-white/20 transition-colors"
                  >
                    <Swords size={18} /> Run Evolution
                  </motion.button>
                </Link>
                <Link to="/docs">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center justify-center gap-2 px-6 py-3 border border-white/10 rounded-xl text-white/80 font-bold text-sm hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <BookOpen size={18} /> Read Docs
                  </motion.button>
                </Link>
              </div>
            </div>

            <div className="hidden lg:flex items-center justify-center mr-8">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
                className="text-white/10"
              >
                <Dna size={180} strokeWidth={0.5} />
              </motion.div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {statCards.map((card, i) => (
          <motion.div
            key={card.title}
            custom={i}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className={`relative overflow-hidden rounded-xl border ${card.border} ${card.bg} p-6 transition-all duration-300 ${card.glow} group shadow-sm`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
                  {card.title}
                </p>
                <p className={`text-3xl font-extrabold font-display text-text-primary`}>
                  {card.value}
                </p>
              </div>
              <div className={`p-3 rounded-xl ${card.iconBg} ${card.color} transition-colors`}>
                <card.icon size={24} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Activity + Quick Pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="rounded-xl border border-border bg-secondary bg-white shadow-sm overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-border flex items-center gap-2 bg-bg-tertiary">
            <Clock size={16} className="text-accent-purple" />
            <h3 className="font-bold font-display text-sm text-text-primary">Recent Activity</h3>
          </div>
          <div className="p-4 space-y-2 max-h-[320px] overflow-y-auto">
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((entry: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.05 }}
                  className="flex items-center gap-3 p-3 rounded-lg border border-border/40 hover:bg-bg-tertiary transition-colors"
                >
                  <div className={`p-2 rounded-lg ${entry.evolutions > 0 ? 'bg-accent-green/10 text-accent-green' : 'bg-bg-tertiary text-text-secondary'}`}>
                    {entry.evolutions > 0 ? <Trophy size={16} /> : <Dna size={16} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{entry.target}</p>
                    <p className="text-xs text-text-secondary">
                      {entry.evolutions} evolution{entry.evolutions !== 1 ? 's' : ''} · Fitness: {entry.fitness?.toFixed(1) ?? '—'}
                    </p>
                  </div>
                  {entry.frozen && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-accent-red bg-accent-red/10 px-2 py-0.5 rounded-full">
                      Frozen
                    </span>
                  )}
                </motion.div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
                <Activity size={32} className="mb-3 opacity-20" />
                <p className="text-sm">No activity yet</p>
                <p className="text-xs mt-1">Upload code and run an evolution to get started</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Evolution Pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="rounded-xl border border-border bg-secondary bg-white shadow-sm overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-border flex items-center gap-2 bg-bg-tertiary">
            <Zap size={16} className="text-accent-purple" />
            <h3 className="font-bold font-display text-sm text-text-primary">The 5-Step Pipeline</h3>
          </div>
          <div className="p-5 space-y-4">
            {[
              { step: '1', label: 'EXTRACT', desc: 'Every function gets DNA — speed, memory, complexity', color: 'accent-cyan', icon: '🧬' },
              { step: '2', label: 'MUTATE', desc: '6 AST mutation strategies spawn code variants', color: 'accent-green', icon: '👾' },
              { step: '3', label: 'EVALUATE', desc: '5-Ring Gauntlet — correctness, speed, memory, edge cases', color: 'accent-yellow', icon: '🏟️' },
              { step: '4', label: 'SELECT', desc: 'Tournament manager picks the winner', color: 'accent-purple', icon: '🏆' },
              { step: '5', label: 'DEPLOY', desc: 'Winner replaces original with backup + rollback', color: 'accent-green', icon: '🚀' },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + i * 0.1 }}
                className="flex items-center gap-4 group"
              >
                <div className={`flex-shrink-0 w-9 h-9 rounded-xl bg-${item.color}/10 border border-${item.color}/20 flex items-center justify-center text-sm`}>
                  {item.icon}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-bold font-display">{item.label}</p>
                  <p className="text-xs text-text-secondary">{item.desc}</p>
                </div>
                {i < 4 && (
                  <ArrowRight size={12} className="text-text-secondary/30 flex-shrink-0" />
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
