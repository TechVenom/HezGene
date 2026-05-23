import { useState, useCallback, useEffect } from 'react';
import { startEvolution, type EvolutionParams } from '../api';
import { useWebSocket } from './useWebSocket';

export interface MutantInfo {
  id: string;
  index: number;
  strategy: string;
  source_code: string;
  loc: number;
  complexity: number;
  // Fight results (filled in during arena_fight)
  passed?: boolean;
  disqualified?: boolean;
  disqualify_reason?: string;
  score?: number;
  speed_ms?: number;
  memory_bytes?: number;
  readability?: number;
  edge_failures?: number;
  rank?: number;
}

export interface EvolutionState {
  isRunning: boolean;
  sessionId: string | null;
  stage: string;
  dna: any | null;
  originalSource: string;
  mutants: MutantInfo[];
  rankings: any[];
  winner: any | null;
  error: string | null;
  finalResults: any[] | null;
}

export function useEvolution() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [dna, setDna] = useState<any>(null);
  const [originalSource, setOriginalSource] = useState('');
  const [mutants, setMutants] = useState<MutantInfo[]>([]);
  const [rankings, setRankings] = useState<any[]>([]);
  const [winner, setWinner] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [finalResults, setFinalResults] = useState<any[] | null>(null);

  const { messages, connected, currentStage, reset: resetWs } = useWebSocket(sessionId);

  // Process messages to update state
  useEffect(() => {
    if (messages.length === 0) return;
    const latest = messages[messages.length - 1];

    switch (latest.stage) {
      case 'dna_extracted':
        setDna(latest.dna);
        if (latest.original_source) setOriginalSource(latest.original_source);
        break;

      case 'mutant_spawned':
        if (latest.mutant) {
          setMutants((prev) => {
            const exists = prev.find((m) => m.id === latest.mutant.id);
            if (exists) return prev;
            return [...prev, latest.mutant as MutantInfo];
          });
        }
        break;

      case 'fight_result':
        if (latest.mutant_result) {
          setMutants((prev) =>
            prev.map((m) =>
              m.id === latest.mutant_result.mutant_id
                ? { ...m, ...latest.mutant_result }
                : m
            )
          );
        }
        break;

      case 'arena_ranked':
        if (latest.rankings) setRankings(latest.rankings);
        break;

      case 'winner_selected':
        if (latest.winner) setWinner(latest.winner);
        if (latest.original_source) setOriginalSource(latest.original_source);
        break;

      case 'complete':
        setIsRunning(false);
        if (latest.results) setFinalResults(latest.results);
        break;

      case 'error':
        setIsRunning(false);
        setError(latest.message || 'Unknown error');
        break;

      case 'no_improvement':
        // Keep running flag as other functions may still be processing
        break;
    }
  }, [messages]);

  const start = useCallback(async (params: EvolutionParams) => {
    // Reset state
    setIsRunning(true);
    setDna(null);
    setOriginalSource('');
    setMutants([]);
    setRankings([]);
    setWinner(null);
    setError(null);
    setFinalResults(null);
    resetWs();

    try {
      const res = await startEvolution(params);
      setSessionId(res.session_id);
    } catch (e: any) {
      setError(e.message || 'Failed to start evolution');
      setIsRunning(false);
    }
  }, [resetWs]);

  const reset = useCallback(() => {
    setSessionId(null);
    setIsRunning(false);
    setDna(null);
    setOriginalSource('');
    setMutants([]);
    setRankings([]);
    setWinner(null);
    setError(null);
    setFinalResults(null);
    resetWs();
  }, [resetWs]);

  return {
    start,
    reset,
    isRunning,
    sessionId,
    stage: currentStage,
    connected,
    dna,
    originalSource,
    mutants,
    rankings,
    winner,
    error,
    finalResults,
    messages,
  };
}
