import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Wifi, WifiOff, Check, Loader2, Save, Brain, Shield, Sliders } from 'lucide-react';
import { getConfig, updateConfig, testLLM } from '../api';

const PROVIDERS = [
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'venomx', label: 'VENOMX' },
];

const COMMON_MODELS: Record<string, {value: string, label: string}[]> = {
  ollama: [
    { value: 'llama3.2', label: 'Llama 3.2' },
    { value: 'gemma2:2b', label: 'Gemma 2 (2B)' },
    { value: 'qwen2.5-coder:1.5b', label: 'Qwen 2.5 Coder' },
    { value: 'qwen2.5-coder:7b', label: 'Qwen 2.5 Coder 7B' },
    { value: 'deepseek-coder', label: 'DeepSeek Coder' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'o1-mini', label: 'o1 Mini' }
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-latest', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' }
  ],
  gemini: [
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' }
  ],
  venomx: [
    { value: 'venomx-code-1', label: 'VENOMX Code 1' },
    { value: 'venomx-code-mini', label: 'VENOMX Code Mini' }
  ]
};

export default function Settings() {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [minImprovement, setMinImprovement] = useState(0.1);
  const [autoApply, setAutoApply] = useState(false);
  const [generations, setGenerations] = useState(5);
  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getConfig().then((res) => {
      if (res.data) {
        setProvider(res.data.llm?.provider || 'ollama');
        setModel(res.data.llm?.model || '');
        setBaseUrl(res.data.llm?.base_url || '');
        setApiKey(res.data.llm?.api_key || '');
        setMinImprovement(res.data.evolution?.min_improvement || 0.001);
        setAutoApply(res.data.safety?.auto_apply || false);
        setGenerations(res.data.evolution?.generations || 5);
      }
    }).catch(() => {});
  }, []);

  const handleTestLLM = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testLLM(provider, model, baseUrl, apiKey);
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ status: 'error', message: e.message });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateConfig('llm.provider', provider);
      await updateConfig('llm.model', model);
      await updateConfig('llm.base_url', baseUrl);
      await updateConfig('llm.api_key', apiKey);
      await updateConfig('evolution.min_improvement', minImprovement);
      await updateConfig('evolution.generations', generations);
      await updateConfig('safety.auto_apply', autoApply);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {} finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto">
        <header className="mb-6">
          <h2 className="text-2xl font-extrabold font-display">Settings</h2>
          <p className="text-text-secondary text-sm mt-0.5">Configure HezGene and LLM integration</p>
        </header>

        <div className="space-y-6">
          {/* LLM Configuration */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-border/50 bg-bg-secondary/40 backdrop-blur-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-border/30 flex items-center gap-2">
              <Brain size={16} className="text-accent-cyan" />
              <h3 className="font-semibold font-display text-sm">LLM Configuration</h3>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Provider</label>
                <select value={provider} onChange={(e) => setProvider(e.target.value)}
                  className="w-full bg-bg-tertiary border border-border/60 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-purple/60">
                  {PROVIDERS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Model Name</label>
                <input type="text" list="models-list" value={model} onChange={(e) => setModel(e.target.value)}
                  placeholder="Select or type a model name..."
                  className="w-full bg-bg-tertiary border border-border/60 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-purple/60" />
                <datalist id="models-list">
                  {COMMON_MODELS[provider]?.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </datalist>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Base URL (optional)</label>
                  <input type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="w-full bg-bg-tertiary border border-border/60 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-purple/60" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">API Key (optional)</label>
                  <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full bg-bg-tertiary border border-border/60 rounded-lg p-2.5 text-sm focus:outline-none focus:border-accent-purple/60" />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
                  onClick={handleTestLLM} disabled={isTesting || !model}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${
                    !model ? 'bg-bg-tertiary text-text-secondary cursor-not-allowed' :
                    'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 hover:bg-accent-cyan/15'
                  }`}>
                  {isTesting ? <Loader2 size={14} className="animate-spin" /> : <Wifi size={14} />}
                  Test Connection
                </motion.button>
                {testResult && (
                  <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className={`text-xs font-medium flex items-center gap-1 ${testResult.status === 'success' ? 'text-accent-green' : 'text-accent-red'}`}>
                    {testResult.status === 'success' ? <Check size={12} /> : <WifiOff size={12} />}
                    {testResult.message}
                  </motion.span>
                )}
              </div>
            </div>
          </motion.section>

          {/* Evolution Parameters */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="rounded-xl border border-border/50 bg-bg-secondary/40 backdrop-blur-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-border/30 flex items-center gap-2">
              <Sliders size={16} className="text-accent-yellow" />
              <h3 className="font-semibold font-display text-sm">Evolution Parameters</h3>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                  Minimum Improvement Threshold: <span className="text-accent-green">{(minImprovement * 100).toFixed(1)}%</span>
                </label>
                <input type="range" min="0" max="0.2" step="0.001" value={minImprovement}
                  onChange={(e) => setMinImprovement(parseFloat(e.target.value))}
                  className="w-full accent-accent-purple h-1.5" />
                <div className="flex justify-between text-[10px] text-text-secondary mt-1"><span>0%</span><span>20%</span></div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                  Mutation Generations: <span className="text-accent-cyan">{generations}</span>
                </label>
                <input type="range" min="1" max="10" step="1" value={generations}
                  onChange={(e) => setGenerations(parseInt(e.target.value))}
                  className="w-full accent-accent-purple h-1.5" />
                <div className="flex justify-between text-[10px] text-text-secondary mt-1"><span>1</span><span>10</span></div>
              </div>
            </div>
          </motion.section>

          {/* Safety Settings */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="rounded-xl border border-border/50 bg-bg-secondary/40 backdrop-blur-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-border/30 flex items-center gap-2">
              <Shield size={16} className="text-accent-green" />
              <h3 className="font-semibold font-display text-sm">Safety & Deployment</h3>
            </div>
            <div className="p-6 space-y-4">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" checked={autoApply} onChange={(e) => setAutoApply(e.target.checked)}
                  className="w-5 h-5 accent-accent-green rounded" />
                <div>
                  <p className="font-medium text-sm">Auto-apply successful evolutions</p>
                  <p className="text-xs text-text-secondary">Deploy winners directly to source files (with backup)</p>
                </div>
              </label>
            </div>
          </motion.section>

          {/* Save Button */}
          <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
            onClick={handleSave} disabled={isSaving}
            className="w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 bg-accent-purple text-white shadow-lg shadow-accent-purple/25 hover:shadow-accent-purple/40 transition-all">
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : saved ? <Check size={16} /> : <Save size={16} />}
            {saved ? 'Saved!' : isSaving ? 'Saving...' : 'Save Configuration'}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
