import { motion } from 'framer-motion';
import { CheckCircle2, Info, Calendar } from 'lucide-react';
import { useMemo, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// Define the components to monitor
const components = [
  { name: 'Core API', subComponents: '12 components', uptime: '99.98%' },
  { name: 'Mutation Engine', subComponents: '12 components', uptime: '99.83%' },
  { name: 'Sandbox Evaluator', subComponents: '5 components', uptime: '99.98%' },
  { name: 'LLM Providers', subComponents: '1 component', uptime: '99.95%' },
];

// Helper to generate 90 bars of history
const generateHistory = (seed: number) => {
  const bars = [];
  let random = seed;
  for (let i = 0; i < 90; i++) {
    // Simple deterministic random
    random = (random * 16807) % 2147483647;
    const val = (random - 1) / 2147483646;
    
    let status = 'operational';
    if (val > 0.98) status = 'major_outage';
    else if (val > 0.95) status = 'partial_outage';
    else if (val > 0.90) status = 'degraded';
    
    bars.push({ date: new Date(Date.now() - (89 - i) * 24 * 60 * 60 * 1000), status });
  }
  return bars;
};

export default function Status() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const dateRangeString = useMemo(() => {
    const today = new Date();
    const ninetyDaysAgo = new Date(today.getTime() - 89 * 24 * 60 * 60 * 1000);
    return `< ${ninetyDaysAgo.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} - ${today.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} >`;
  }, []);

  const componentHistories = useMemo(() => {
    return components.map((comp, i) => ({
      ...comp,
      history: generateHistory(1000 + i * 42),
    }));
  }, []);

  return (
    <div className="p-8 max-w-5xl mx-auto font-sans">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-text-primary mb-2">System Status</h1>
      </motion.div>

      {/* Operational Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8 rounded-xl border border-accent-green/30 bg-[#eefaf4] overflow-hidden shadow-sm"
      >
        <div className="p-5 flex items-center gap-3 border-b border-accent-green/20">
          <CheckCircle2 className="text-accent-green fill-accent-green/20" size={24} />
          <h2 className="text-lg font-bold text-text-primary">We're fully operational</h2>
        </div>
        <div className="p-5 bg-white">
          <p className="text-text-secondary text-sm font-medium">
            We're not aware of any issues affecting our systems.
          </p>
        </div>
      </motion.div>

      {/* Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-xl border border-border bg-white shadow-sm overflow-hidden"
      >
        <div className="p-5 border-b border-border flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-text-primary">System status</h2>
            <div className="flex items-center text-sm text-text-secondary">
              <span className="font-medium">{dateRangeString}</span>
            </div>
          </div>
          <div className="text-sm font-mono font-bold text-text-secondary">
            {currentTime.toLocaleTimeString()}
          </div>
        </div>

        <div className="p-6 space-y-10">
          {componentHistories.map((comp, idx) => (
            <div key={idx} className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="text-accent-green fill-accent-green/20" size={18} />
                  <span className="font-bold text-text-primary">{comp.name}</span>
                  <Info size={14} className="text-text-secondary/50" />
                  <span className="text-sm text-text-secondary ml-1">{comp.subComponents} ⌄</span>
                </div>
                <span className="text-sm font-medium text-text-secondary">{comp.uptime} uptime</span>
              </div>
              
              <div className="flex items-center justify-between gap-[3px] h-[34px]">
                {comp.history.map((day, i) => {
                  let bgColor = 'bg-accent-green/80'; // operational
                  if (day.status === 'degraded') bgColor = 'bg-accent-yellow/80';
                  if (day.status === 'partial_outage') bgColor = 'bg-accent-yellow';
                  if (day.status === 'major_outage') bgColor = 'bg-accent-red/80';

                  return (
                    <div 
                      key={i} 
                      className={`flex-1 h-full rounded-[2px] ${bgColor} hover:opacity-70 transition-opacity cursor-pointer`}
                      title={`${day.date.toLocaleDateString()}: ${day.status}`}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* View History Button */}
      <div className="mt-8 flex justify-center pb-12">
        <Link to="/history">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-border rounded-lg text-sm font-bold text-text-primary shadow-sm hover:bg-bg-tertiary transition-colors">
            <Calendar size={16} /> View history
          </button>
        </Link>
      </div>
    </div>
  );
}
