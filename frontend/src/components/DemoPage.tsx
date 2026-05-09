import { useCallback, useEffect, useRef, useState } from 'react';
import ImageUpload from './ImageUpload';
import StatusBadge from './StatusBadge';
import ErrorToast from './ErrorToast';
import HeatmapBloom from './HeatmapBloom';
import TypewriterText from './TypewriterText';
import SoundEngine from '../lib/sound';
import type { VerifyResponse } from '../lib/api';
import { catalogProduct, verifyReturn } from '../lib/api';

type VerifyState = 'idle' | 'cataloging' | 'analyzing' | 'done' | 'error';

interface Preset {
  label: string;
  productId: string;
  catalogFile: string;
  returnFile: string;
}

const PRESETS: Record<string, Preset> = {
  '1': { label: 'Genuine match', productId: 'saree_000', catalogFile: '/fixtures/saree/saree_000.jpeg', returnFile: '/fixtures/saree/saree_000.jpeg' },
  '2': { label: 'Same-category fraud', productId: 'saree_000', catalogFile: '/fixtures/saree/saree_000.jpeg', returnFile: '/fixtures/saree/saree_005.jpeg' },
  '3': { label: 'Cross-category swap', productId: 'sherwani_001', catalogFile: '/fixtures/sherwani/sherwani_001.jpeg', returnFile: '/fixtures/saree/saree_003.jpeg' },
};

export default function DemoPage() {
  const [productId, setProductId] = useState('');
  const [catalogFile, setCatalogFile] = useState<File | null>(null);
  const [returnFile, setReturnFile] = useState<File | null>(null);
  const [state, setState] = useState<VerifyState>('idle');
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [directorMode, setDirectorMode] = useState(false);
  const [lastPreset, setLastPreset] = useState<string | null>(null);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const [soundMuted, setSoundMuted] = useState(() => typeof window !== 'undefined' && window.innerWidth < 768);

  const soundRef = useRef<SoundEngine>(new SoundEngine(typeof window !== 'undefined' && window.innerWidth < 768));
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Elapsed timer
  const startTimer = useCallback(() => {
    const t0 = Date.now();
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed(((Date.now() - t0) / 1000)), 100);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  }, []);

  // Core verify logic
  const runVerification = useCallback(async (pid: string, catFile: File, retFile: File) => {
    try {
      setState('cataloging');
      startTimer();
      soundRef.current.play('hum');

      // Auto-catalog: always catalog first (backend handles idempotency)
      await catalogProduct(pid, catFile);

      setState('analyzing');
      const res = await verifyReturn(pid, retFile);

      stopTimer();
      soundRef.current.stopHum();
      soundRef.current.play(res.decision === 'MATCH' ? 'ping' : 'alert');

      setResult(res);
      setState('done');
    } catch (err) {
      stopTimer();
      soundRef.current.stopHum();
      setError(err instanceof Error ? err.message : 'Verification failed');
      setState('error');
    }
  }, [startTimer, stopTimer]);

  // Manual verify
  const handleVerify = useCallback(() => {
    if (!productId || !catalogFile || !returnFile) return;
    setResult(null);
    setError(null);
    runVerification(productId, catalogFile, returnFile);
  }, [productId, catalogFile, returnFile, runVerification]);

  // Director mode: keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.key === 'd' || e.key === 'D') {
        setDirectorMode(prev => !prev);
        return;
      }

      if (!directorMode) return;

      if (e.key === 's' || e.key === 'S') {
        setSpeedMultiplier(2);
        return;
      }
      if (e.key === 'n' || e.key === 'N') {
        setSpeedMultiplier(1);
        return;
      }

      const preset = PRESETS[e.key];
      if (preset) {
        triggerPreset(e.key, preset);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [directorMode]);

  const triggerPreset = async (key: string, preset: Preset) => {
    setLastPreset(key);
    setResult(null);
    setError(null);
    setProductId(preset.productId);

    try {
      const [catResp, retResp] = await Promise.all([
        fetch(preset.catalogFile),
        fetch(preset.returnFile),
      ]);
      const catBlob = await catResp.blob();
      const retBlob = await retResp.blob();
      const catF = new File([catBlob], preset.catalogFile.split('/').pop()!, { type: 'image/jpeg' });
      const retF = new File([retBlob], preset.returnFile.split('/').pop()!, { type: 'image/jpeg' });

      setCatalogFile(catF);
      setReturnFile(retF);
      runVerification(preset.productId, catF, retF);
    } catch {
      setError('Failed to load preset images');
    }
  };

  const handleReplay = () => {
    if (!lastPreset || !PRESETS[lastPreset]) return;
    triggerPreset(lastPreset, PRESETS[lastPreset]);
  };

  const toggleSound = () => {
    const muted = soundRef.current.toggle();
    setSoundMuted(muted);
  };

  const isProcessing = state === 'cataloging' || state === 'analyzing';

  return (
    <div className="min-h-[calc(100vh-3.5rem)] p-4 lg:p-8 max-w-7xl mx-auto">
      <ErrorToast message={error} onDismiss={() => setError(null)} />

      {/* Director mode indicator */}
      {directorMode && (
        <div className="fixed top-16 right-4 z-50 bg-danger/20 border border-danger/40 text-danger px-3 py-1 rounded-full text-xs font-data animate-pulse">
          DIRECTOR
        </div>
      )}

      {/* Two-panel layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
        {/* Left: Catalog */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-muted uppercase tracking-wider">Catalog Product</h2>
          <div>
            <label className="text-sm text-muted mb-1 block">Product ID</label>
            <input
              type="text"
              value={productId}
              onChange={e => setProductId(e.target.value)}
              placeholder="e.g. Saree_000"
              className="w-full px-3 py-2 rounded-lg bg-surface border border-border text-text placeholder-muted/40 focus:outline-none focus:border-accent text-sm font-data"
            />
          </div>
          <ImageUpload
            label="Catalog Image"
            onFileSelect={setCatalogFile}
            onFileClear={() => setCatalogFile(null)}
            file={catalogFile}
          />
        </div>

        {/* Right: Return */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-muted uppercase tracking-wider">Return Item</h2>
          <ImageUpload
            label="Return Image"
            onFileSelect={setReturnFile}
            onFileClear={() => setReturnFile(null)}
            file={returnFile}
          />
        </div>
      </div>

      {/* Verify button */}
      <div className="mt-6 flex items-center justify-center gap-3">
        <button
          onClick={handleVerify}
          disabled={isProcessing || !productId || !catalogFile || !returnFile}
          className="bg-accent hover:bg-accent/90 disabled:bg-muted/20 disabled:text-muted px-8 py-3 rounded-lg font-semibold text-bg disabled:text-bg/40 transition-colors"
        >
          {state === 'cataloging' ? 'Cataloging...' : state === 'analyzing' ? 'Analyzing...' : 'Verify Return'}
        </button>

        <button
          onClick={toggleSound}
          className="p-2 rounded-lg border border-border text-muted hover:text-text transition-colors"
          aria-label="Toggle sound"
        >
          {soundMuted ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          )}
        </button>

        {directorMode && lastPreset && (
          <button
            onClick={handleReplay}
            className="px-4 py-2 rounded-lg border border-accent/30 text-accent hover:bg-accent/10 text-sm font-medium transition-colors"
          >
            Replay
          </button>
        )}
      </div>

      {/* Processing state */}
      {isProcessing && (
        <div className="mt-8 flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted font-data">
            {state === 'cataloging' ? 'Cataloging product...' : 'Analyzing with I-JEPA...'}
          </p>
          <p className="font-data text-accent text-lg">{elapsed.toFixed(1)}s</p>
        </div>
      )}

      {/* Results */}
      {state === 'done' && result && (
        <div className="mt-8 space-y-6">
          {/* Decision */}
          <div className="flex items-center gap-4 justify-center">
            <StatusBadge decision={result.decision as 'MATCH' | 'SUSPECT' | 'REJECT'} />
            <div className="text-center">
              <p className="font-data text-3xl text-text">{result.confidence.toFixed(3)}</p>
              <p className="text-xs text-muted">confidence</p>
            </div>
            <div className="text-center">
              <p className="font-data text-lg text-text">{result.latency_ms.toFixed(0)}ms</p>
              <p className="text-xs text-muted">latency</p>
            </div>
            {result.baseline_threshold != null && (
              <div className="text-center">
                <p className="font-data text-lg text-muted">{result.baseline_threshold.toFixed(2)}</p>
                <p className="text-xs text-muted">threshold</p>
              </div>
            )}
          </div>

          {/* Heatmap + Explanation grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Heatmap */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted">Spatial Diff Heatmap</h3>
              <HeatmapBloom
                base64Image={result.spatial_diff_image}
                speedMultiplier={speedMultiplier}
              />
            </div>

            {/* Explanation */}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted">AI Explanation</h3>
              <div className="rounded-lg border border-border bg-surface p-4 min-h-[200px]">
                <TypewriterText
                  text={result.explanation}
                  attribution="Gemma 4 · VLM Explanation"
                  speedMultiplier={speedMultiplier}
                />
              </div>
              {result.suspect_reason && (
                <p className="text-xs text-warning font-data">
                  Reason: {result.suspect_reason}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Director mode help */}
      {directorMode && (
        <div className="mt-8 p-4 rounded-lg border border-border bg-surface text-xs font-data text-muted space-y-1">
          <p className="text-accent font-semibold text-sm mb-2">Director Mode</p>
          <p><span className="text-text">1</span> Genuine match (Saree_000 → Saree_000)</p>
          <p><span className="text-text">2</span> Same-category fraud (Saree_000 → Saree_005)</p>
          <p><span className="text-text">3</span> Cross-category swap (Sherwani_001 → Saree_003)</p>
          <p><span className="text-text">S</span> Slow mode · <span className="text-text">N</span> Normal speed</p>
          <p><span className="text-text">D</span> Exit director mode</p>
        </div>
      )}
    </div>
  );
}
