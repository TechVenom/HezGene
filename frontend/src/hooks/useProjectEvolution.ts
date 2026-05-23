import { useState, useCallback, useEffect } from 'react';
import { evolveProject, pauseProjectEvolution, resumeProjectEvolution, cancelProjectEvolution } from '../api';
import { useWebSocket } from './useWebSocket';
import { MutantInfo } from './useEvolution';

export interface ProjectEvolutionState {
  isRunning: boolean;
  isPaused: boolean;
  sessionId: string | null;
  stage: string;
  projectName: string;
  totalFunctions: number;
  completedFunctions: number;
  currentFunction: string | null;
  currentFile: string | null;
  functionStatuses: Record<string, { status: string; winner?: any; mutants?: MutantInfo[] }>;
  error: string | null;
  finalResults: any[] | null;
}

export function useProjectEvolution() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [totalFunctions, setTotalFunctions] = useState(0);
  const [completedFunctions, setCompletedFunctions] = useState(0);
  const [currentFunction, setCurrentFunction] = useState<string | null>(null);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [functionStatuses, setFunctionStatuses] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);
  const [finalResults, setFinalResults] = useState<any[] | null>(null);

  const { messages, connected, currentStage, reset: resetWs } = useWebSocket(sessionId);

  useEffect(() => {
    if (messages.length === 0) return;
    const latest = messages[messages.length - 1];

    switch (latest.stage) {
      case 'project_started':
        setProjectName(latest.project_name);
        setTotalFunctions(latest.total_functions);
        break;

      case 'function_started':
        setCurrentFile(latest.file_path);
        setCurrentFunction(latest.function);
        setCompletedFunctions(latest.progress);
        setFunctionStatuses(prev => ({
          ...prev,
          [`${latest.file_path}:${latest.function}`]: { status: 'running', mutants: [] }
        }));
        break;

      case 'spawning_mutants':
      case 'arena_fight':
        setFunctionStatuses(prev => ({
          ...prev,
          [`${latest.file_path || currentFile}:${latest.function || currentFunction}`]: { 
            ...prev[`${latest.file_path || currentFile}:${latest.function || currentFunction}`],
            status: latest.stage 
          }
        }));
        break;

      case 'mutant_spawned':
        if (latest.mutant) {
          const key = `${latest.file_path || currentFile}:${latest.function || currentFunction}`;
          setFunctionStatuses(prev => {
            const current = prev[key] || { mutants: [] };
            const existing = current.mutants?.find((m: any) => m.id === latest.mutant.id);
            if (existing) return prev;
            return {
              ...prev,
              [key]: { ...current, mutants: [...(current.mutants || []), latest.mutant] }
            };
          });
        }
        break;

      case 'function_complete':
        setFunctionStatuses(prev => ({
          ...prev,
          [`${latest.file_path}:${latest.function}`]: {
            status: latest.status,
            improvements: latest.improvements
          }
        }));
        break;

      case 'function_error':
        setFunctionStatuses(prev => ({
          ...prev,
          [`${latest.file_path}:${latest.function}`]: { status: 'error', error: latest.error }
        }));
        break;

      case 'project_complete':
        setIsRunning(false);
        setCompletedFunctions(totalFunctions); // ensure 100%
        if (latest.results) setFinalResults(latest.results);
        break;

      case 'project_cancelled':
        setIsRunning(false);
        setIsPaused(false);
        break;

      case 'error':
        setIsRunning(false);
        setError(latest.message || 'Unknown error');
        break;
    }
  }, [messages, currentFile, currentFunction, totalFunctions]);

  const start = useCallback(async (params: any) => {
    setIsRunning(true);
    setIsPaused(false);
    setProjectName('');
    setTotalFunctions(0);
    setCompletedFunctions(0);
    setCurrentFunction(null);
    setCurrentFile(null);
    setFunctionStatuses({});
    setError(null);
    setFinalResults(null);
    resetWs();

    try {
      const res = await evolveProject(params);
      setSessionId(res.session_id);
    } catch (e: any) {
      setError(e.message || 'Failed to start project evolution');
      setIsRunning(false);
    }
  }, [resetWs]);

  const pause = useCallback(async () => {
    if (!sessionId) return;
    await pauseProjectEvolution(sessionId);
    setIsPaused(true);
  }, [sessionId]);

  const resume = useCallback(async () => {
    if (!sessionId) return;
    await resumeProjectEvolution(sessionId);
    setIsPaused(false);
  }, [sessionId]);

  const cancel = useCallback(async () => {
    if (!sessionId) return;
    await cancelProjectEvolution(sessionId);
    setIsRunning(false);
    setIsPaused(false);
  }, [sessionId]);

  const reset = useCallback(() => {
    setSessionId(null);
    setIsRunning(false);
    setIsPaused(false);
    setProjectName('');
    setTotalFunctions(0);
    setCompletedFunctions(0);
    setCurrentFunction(null);
    setCurrentFile(null);
    setFunctionStatuses({});
    setError(null);
    setFinalResults(null);
    resetWs();
  }, [resetWs]);

  return {
    start,
    pause,
    resume,
    cancel,
    reset,
    isRunning,
    isPaused,
    sessionId,
    stage: currentStage,
    connected,
    projectName,
    totalFunctions,
    completedFunctions,
    currentFunction,
    currentFile,
    functionStatuses,
    error,
    finalResults,
    messages,
  };
}
