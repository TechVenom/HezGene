import { motion } from 'framer-motion';
import { Terminal, Code2, Cpu, Zap, Activity } from 'lucide-react';

export default function Docs() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <h1 className="text-4xl font-extrabold font-display text-text-primary mb-3">Documentation</h1>
        <p className="text-text-secondary text-lg">
          Master the HezGene Autonomous Agent and integrate via the REST API.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Navigation Sidebar (in page) */}
        <div className="lg:col-span-1 hidden lg:block">
          <div className="sticky top-8 bg-white border border-border rounded-xl p-4 shadow-sm">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-4">Contents</h3>
            <nav className="space-y-2">
              <a href="#agent-usage" className="block text-sm text-text-primary hover:text-accent-purple font-medium">Agent Usage</a>
              <a href="#mutation-engine" className="block text-sm text-text-secondary hover:text-accent-purple ml-3">Mutation Engine</a>
              <a href="#gauntlet" className="block text-sm text-text-secondary hover:text-accent-purple ml-3">The Gauntlet</a>
              <a href="#api-reference" className="block text-sm text-text-primary hover:text-accent-purple font-medium mt-4">API Reference</a>
              <a href="#endpoints" className="block text-sm text-text-secondary hover:text-accent-purple ml-3">Endpoints</a>
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3 space-y-12">
          
          {/* Agent Section */}
          <section id="agent-usage" className="scroll-mt-8">
            <div className="flex items-center gap-3 mb-6 border-b border-border pb-4">
              <div className="p-2.5 bg-accent-purple/10 rounded-xl text-accent-purple">
                <Cpu size={24} />
              </div>
              <h2 className="text-2xl font-bold font-display text-text-primary">Agent Usage</h2>
            </div>
            
            <div className="prose prose-sm max-w-none text-text-primary space-y-6">
              <p>
                The HezGene Autonomous Agent is designed to refactor, optimize, and heal your Python codebase without human intervention.
              </p>

              <h3 id="mutation-engine" className="text-lg font-bold mt-8 mb-4">1. The Mutation Engine</h3>
              <p className="text-text-secondary">
                When you target a function in the Evolution Arena, the agent spawns multiple variants ("mutants") of the original code using two primary engines:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="p-5 bg-white border border-border rounded-xl shadow-sm">
                  <h4 className="font-bold flex items-center gap-2 mb-2"><Code2 size={16} className="text-accent-cyan"/> AST Engine</h4>
                  <p className="text-xs text-text-secondary">Applies deterministic transformations directly to the Abstract Syntax Tree (e.g., constant folding, early returns, loop comprehensions). These are guaranteed to be syntactically valid.</p>
                </div>
                <div className="p-5 bg-white border border-border rounded-xl shadow-sm">
                  <h4 className="font-bold flex items-center gap-2 mb-2"><Zap size={16} className="text-accent-purple"/> LLM Engine</h4>
                  <p className="text-xs text-text-secondary">Leverages Generative AI to rewrite algorithms, improve semantic readability, and find creative performance optimizations that strict compilers miss.</p>
                </div>
              </div>

              <h3 id="gauntlet" className="text-lg font-bold mt-8 mb-4">2. The 5-Ring Gauntlet</h3>
              <p className="text-text-secondary">
                Mutants are evaluated in an isolated sandbox. To be considered for deployment, a mutant must pass all functional tests (Correctness) and then compete on performance:
              </p>
              <ul className="list-disc pl-5 space-y-2 text-sm text-text-secondary">
                <li><strong className="text-text-primary">Execution Speed:</strong> Measured in milliseconds.</li>
                <li><strong className="text-text-primary">Memory Footprint:</strong> Peak memory usage during execution.</li>
                <li><strong className="text-text-primary">Complexity:</strong> Cyclomatic complexity reduction.</li>
              </ul>
              
              <div className="p-4 bg-accent-green/10 border border-accent-green/30 rounded-xl mt-6">
                <p className="text-sm font-bold text-accent-green flex items-center gap-2">
                  <Activity size={16} /> Auto-Deployment
                </p>
                <p className="text-xs text-text-secondary mt-1">
                  If <strong>Auto-Deploy</strong> is enabled in the settings, the agent will surgically overwrite your local Python file with the winning mutant, while creating a safety backup in the `.hezgene` directory.
                </p>
              </div>
            </div>
          </section>

          {/* API Section */}
          <section id="api-reference" className="scroll-mt-8">
            <div className="flex items-center gap-3 mb-6 border-b border-border pb-4">
              <div className="p-2.5 bg-accent-cyan/10 rounded-xl text-accent-cyan">
                <Terminal size={24} />
              </div>
              <h2 className="text-2xl font-bold font-display text-text-primary">API Reference</h2>
            </div>

            <div className="space-y-6">
              <p className="text-sm text-text-secondary">
                HezGene exposes a RESTful API on port 8000. You can integrate HezGene directly into your CI/CD pipelines.
              </p>

              <div id="endpoints" className="space-y-4">
                {/* Endpoint 1 */}
                <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
                  <div className="bg-bg-tertiary px-4 py-3 border-b border-border flex items-center gap-3">
                    <span className="px-2 py-1 bg-accent-green/10 text-accent-green font-bold text-[10px] rounded uppercase tracking-wider">GET</span>
                    <span className="font-mono text-sm font-bold text-text-primary">/api/files</span>
                  </div>
                  <div className="p-4">
                    <p className="text-xs text-text-secondary mb-2">Returns a list of all parsed Python files in the current workspace.</p>
                    <pre className="bg-bg-primary p-3 rounded-lg text-[10px] font-mono text-text-primary overflow-x-auto">
{`{
  "status": "success",
  "data": [
    { "id": "src/main.py", "name": "main.py", "functions": 12 }
  ]
}`}
                    </pre>
                  </div>
                </div>

                {/* Endpoint 2 */}
                <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
                  <div className="bg-bg-tertiary px-4 py-3 border-b border-border flex items-center gap-3">
                    <span className="px-2 py-1 bg-accent-yellow/10 text-accent-yellow font-bold text-[10px] rounded uppercase tracking-wider">POST</span>
                    <span className="font-mono text-sm font-bold text-text-primary">/api/evolve/start</span>
                  </div>
                  <div className="p-4">
                    <p className="text-xs text-text-secondary mb-2">Triggers a background evolution task for a specific target.</p>
                    <p className="text-xs font-bold mb-1">Payload:</p>
                    <pre className="bg-bg-primary p-3 rounded-lg text-[10px] font-mono text-text-primary overflow-x-auto mb-3">
{`{
  "target": "src/math_utils.py:calculate_fibonacci",
  "use_llm": false,
  "generations": 5
}`}
                    </pre>
                  </div>
                </div>

                {/* Endpoint 3 */}
                <div className="bg-white border border-border rounded-xl overflow-hidden shadow-sm">
                  <div className="bg-bg-tertiary px-4 py-3 border-b border-border flex items-center gap-3">
                    <span className="px-2 py-1 bg-accent-purple/10 text-accent-purple font-bold text-[10px] rounded uppercase tracking-wider">GET</span>
                    <span className="font-mono text-sm font-bold text-text-primary">/api/evolve/stream</span>
                  </div>
                  <div className="p-4">
                    <p className="text-xs text-text-secondary mb-2">Server-Sent Events (SSE) endpoint to receive live updates from the evolution pipeline.</p>
                  </div>
                </div>

              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
