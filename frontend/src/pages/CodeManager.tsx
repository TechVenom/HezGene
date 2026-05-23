import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, FileCode, Trash2, Dna, Swords, ChevronDown,
  ChevronRight, Snowflake, Search, RotateCcw, FolderCode, Github, Folder, Zap
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import {
  getFiles, getProjectTree, uploadProjectZip, connectGitHub,
  deleteFile, scanFile, clearSandbox, cleanSystem, freezeFunction, unfreezeFunction
} from '../api';

export default function CodeManager() {
  const navigate = useNavigate();
  const [projectTree, setProjectTree] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [githubUrl, setGithubUrl] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['.'])); // Root expanded by default

  const fetchProjectTree = useCallback(async () => {
    try {
      const res = await getProjectTree('.');
      if (res.data) setProjectTree(res.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => { fetchProjectTree(); }, [fetchProjectTree]);

  const handleUploadZip = async (file: File) => {
    setIsUploading(true);
    try {
      const res = await uploadProjectZip(file);
      setProjectTree(res.data);
    } catch (err: any) {
      alert(err.message || 'Failed to upload project zip');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip')) {
        handleUploadZip(file);
      } else {
        alert('Please upload a .zip file containing your project.');
      }
    }
  };

  const handleConnectGithub = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl) return;
    setIsConnecting(true);
    try {
      const res = await connectGitHub(githubUrl);
      setProjectTree(res.data);
      setGithubUrl('');
    } catch (err: any) {
      alert(err.message || 'Failed to connect to GitHub');
    } finally {
      setIsConnecting(false);
    }
  };

  const toggleNode = (path: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) newSet.delete(path);
      else newSet.add(path);
      return newSet;
    });
  };

  const handleClearSandbox = async () => {
    if (window.confirm('Wipe all temporary files from the sandbox? Original code will not be modified.')) {
      try {
        const res = await clearSandbox();
        alert(res.message || 'Sandbox cleared successfully.');
      } catch (err: any) {
        alert(err.message || 'Failed to clear sandbox.');
      }
    }
  };

  const handleClearRegistry = async () => {
    if (window.confirm('Factory Reset: Wipe everything including uploads, backups, sandbox files, and DNA registry? This cannot be undone.')) {
      try {
        const res = await cleanSystem();
        setProjectTree(null);
        alert(res.message || 'System completely wiped.');
      } catch (err: any) {
        alert(err.message || 'Failed to wipe system.');
      }
    }
  };

  const renderIndicator = (indicator: string | null) => {
    if (indicator === 'excellent') return <span className="text-accent-green" title="Excellent Fitness">🟢</span>;
    if (indicator === 'fair') return <span className="text-accent-yellow" title="Fair Fitness">🟡</span>;
    if (indicator === 'poor') return <span className="text-accent-red" title="Poor Fitness">🔴</span>;
    return <span className="text-text-secondary opacity-50" title="Unknown Fitness">⚪</span>;
  };

  const renderTree = (node: any, level = 0) => {
    if (!node) return null;
    const isExpanded = expandedNodes.has(node.path);

    if (node.type === 'directory') {
      return (
        <div key={node.path} className="w-full">
          <div 
            className="flex items-center gap-2 py-2 px-3 hover:bg-bg-tertiary/40 cursor-pointer rounded-lg text-sm font-medium transition-colors"
            style={{ paddingLeft: `${level * 16 + 12}px` }}
            onClick={() => toggleNode(node.path)}
          >
            {isExpanded ? <ChevronDown size={16} className="text-text-secondary" /> : <ChevronRight size={16} className="text-text-secondary" />}
            <Folder size={16} className="text-accent-cyan" />
            <span>{node.name}/</span>
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                {node.children.map((child: any) => renderTree(child, level + 1))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      );
    } else if (node.type === 'file') {
      return (
        <div key={node.path} className="w-full group">
          <div 
            className="flex items-center gap-3 py-2 px-3 hover:bg-bg-tertiary/40 rounded-lg text-sm transition-colors"
            style={{ paddingLeft: `${level * 16 + 32}px` }}
          >
            <FileCode size={16} className="text-text-secondary/70" />
            <span className="flex-1 font-mono text-xs">{node.name}</span>
            <div className="flex items-center gap-4 text-xs text-text-secondary">
              <span className="w-24 text-right">{node.evolvable_functions} functions</span>
              <span className="flex items-center gap-1.5 w-24 text-right justify-end">
                {renderIndicator(node.fitness_indicator)} Avg: {node.avg_fitness !== null ? node.avg_fitness.toFixed(1) : '--'}
              </span>
              <div className="opacity-0 group-hover:opacity-100 flex gap-2 transition-opacity ml-2">
                <button 
                  onClick={() => navigate(`/arena?target=${encodeURIComponent(node.path)}`)}
                  className="p-1 rounded bg-accent-purple/10 text-accent-purple hover:bg-accent-purple/20 transition-colors"
                  title="Evolve this file"
                >
                  <Swords size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="p-6 h-full flex flex-col max-w-5xl mx-auto w-full">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold font-display flex items-center gap-2">
            <FolderCode className="text-accent-cyan" /> Project Explorer
          </h2>
          <p className="text-text-secondary text-sm mt-1">Upload and manage your entire codebase for evolution</p>
        </div>
        <div className="flex gap-2">
          {projectTree && (
            <Link to="/arena?target=.">
              <button
                className="px-4 py-2 rounded-lg border border-accent-purple/30 bg-accent-purple text-bg-primary font-bold shadow-lg shadow-accent-purple/20 flex items-center gap-2 hover:bg-accent-purple/90 transition-all"
                title="Evolve entire project workspace"
              >
                <Zap size={16} className="fill-current" />
                Evolve Project
              </button>
            </Link>
          )}
          <button
            onClick={handleClearSandbox}
            className="px-3 py-2 rounded-lg border border-border/50 text-text-secondary hover:bg-bg-secondary text-sm font-semibold flex items-center gap-1.5 transition-all"
          >
            <Trash2 size={14} />
            Sandbox
          </button>
          <button
            onClick={handleClearRegistry}
            className="px-3 py-2 rounded-lg border border-accent-red/20 text-accent-red hover:bg-accent-red/10 text-sm font-semibold flex items-center gap-1.5 transition-all"
          >
            <RotateCcw size={14} />
            Wipe
          </button>
        </div>
      </header>

      {/* Ingestion Zone */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Zip Upload */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`relative rounded-xl border-2 border-dashed p-6 text-center transition-all cursor-pointer flex flex-col justify-center items-center h-32 ${
            isDragging ? 'border-accent-purple bg-accent-purple/5 scale-[1.02]' : 'border-border/50 bg-bg-secondary/30 hover:border-accent-purple/40'
          }`}
        >
          <input
            type="file"
            accept=".zip"
            onChange={(e) => e.target.files && handleUploadZip(e.target.files[0])}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isUploading}
          />
          <Upload size={28} className={`mb-2 ${isDragging ? 'text-accent-purple' : 'text-text-secondary/50'}`} />
          <p className="text-sm font-bold text-text-primary">
            {isUploading ? 'Extracting project...' : 'Upload Project ZIP'}
          </p>
          <p className="text-xs text-text-secondary mt-1">Drag & drop your source code</p>
        </div>

        {/* GitHub Connect */}
        <div className="rounded-xl border border-border/50 bg-bg-secondary/30 p-6 flex flex-col justify-center h-32">
          <div className="flex items-center gap-2 mb-3">
            <Github size={20} className="text-text-primary" />
            <span className="text-sm font-bold">Connect GitHub</span>
          </div>
          <form onSubmit={handleConnectGithub} className="flex gap-2">
            <input
              type="text"
              placeholder="https://github.com/user/repo"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              className="flex-1 bg-bg-primary border border-border/50 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent-cyan"
              disabled={isConnecting}
            />
            <button
              type="submit"
              disabled={isConnecting || !githubUrl}
              className="px-4 py-2 bg-text-primary text-bg-primary rounded-lg text-sm font-bold disabled:opacity-50 transition-opacity"
            >
              {isConnecting ? 'Cloning...' : 'Clone'}
            </button>
          </form>
        </div>
      </div>

      {/* Project Tree View */}
      <div className="flex-1 rounded-xl border border-border/50 bg-bg-secondary/20 backdrop-blur-sm overflow-hidden flex flex-col min-h-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        {projectTree ? (
          <>
            <div className="border-b border-border/30 bg-bg-secondary/50 p-4 flex items-center justify-between shrink-0">
              <h3 className="font-bold flex items-center gap-2">
                <FolderCode size={18} className="text-accent-cyan" /> 
                {projectTree.project_name}
              </h3>
              <div className="flex items-center gap-6 text-sm text-text-secondary">
                <span><strong className="text-text-primary">{projectTree.total_files}</strong> files</span>
                <span><strong className="text-text-primary">{projectTree.total_functions}</strong> functions</span>
                <span><strong className="text-text-primary">{projectTree.total_classes}</strong> classes</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono">
              {renderTree(projectTree.tree)}
            </div>

            <div className="border-t border-border/30 bg-bg-secondary/50 p-4 shrink-0 flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm font-medium">
                <span className="flex items-center gap-1.5"><span className="text-accent-green">🟢</span> Excellent: {projectTree.fitness_excellent}</span>
                <span className="flex items-center gap-1.5"><span className="text-accent-yellow">🟡</span> Fair: {projectTree.fitness_fair}</span>
                <span className="flex items-center gap-1.5"><span className="text-accent-red">🔴</span> Poor: {projectTree.fitness_poor}</span>
              </div>
              {projectTree.recommendation && (
                <div className="text-sm font-medium text-accent-purple bg-accent-purple/10 px-3 py-1.5 rounded-lg border border-accent-purple/20">
                  💡 Recommended: {projectTree.recommendation}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-text-secondary opacity-60">
            <FolderCode size={48} className="mb-4 opacity-50" />
            <p>Upload a ZIP or connect a GitHub repository to load a project tree.</p>
          </div>
        )}
      </div>
    </div>
  );
}
