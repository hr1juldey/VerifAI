import { useEffect, useRef, useState, useCallback, useMemo } from 'react';

// --- Data: all fixture categories ---
const CATEGORIES = [
  { name: 'saree', images: Array.from({ length: 10 }, (_, i) => `/fixtures/saree/saree_00${i}.jpeg`) },
  { name: 'kurta', images: Array.from({ length: 10 }, (_, i) => `/fixtures/kurta/kurta_00${i}.jpeg`) },
  { name: 'lehenga', images: Array.from({ length: 10 }, (_, i) => `/fixtures/lehenga/lehenga_00${i}.jpeg`) },
  { name: 'sherwani', images: Array.from({ length: 10 }, (_, i) => `/fixtures/sherwani/sherwani_00${i}.jpeg`) },
] as const;

type VerdictType = 'genuine' | 'suspect' | 'fraud';

interface Scenario {
  catalogImg: string;
  returnImg: string;
  verdict: VerdictType;
  confidence: string;
  heatmapStyle: React.CSSProperties;
  badgeLabel: string;
  badgeClasses: string;
  pulseShadow: string;
}

function randInt(max: number) {
  return Math.floor(Math.random() * max);
}

function generateScenario(): Scenario {
  const scenarioType = (['genuine', 'suspect', 'fraud'] as VerdictType[])[randInt(3)];
  const catIdx = randInt(CATEGORIES.length);
  const cat = CATEGORIES[catIdx];
  const imgIdx = randInt(10);

  let catalogImg: string;
  let returnImg: string;
  let confidence: string;
  let heatmapStyle: React.CSSProperties;
  let badgeLabel: string;
  let badgeClasses: string;
  let pulseShadow: string;

  switch (scenarioType) {
    case 'genuine': {
      // Same image for both
      catalogImg = cat.images[imgIdx];
      returnImg = cat.images[imgIdx];
      const conf = (0.95 + Math.random() * 0.04).toFixed(2);
      confidence = conf;
      badgeLabel = 'MATCH';
      badgeClasses = 'bg-success/20 text-success border-success/30';
      pulseShadow = 'rgba(74,222,128,0.4)';
      // Very faint cool overlay — barely visible
      heatmapStyle = {
        background: `
          radial-gradient(ellipse at 50% 50%, rgba(74,222,128,0.08) 0%, transparent 70%)
        `,
      };
      break;
    }
    case 'suspect': {
      // Different images, same category
      catalogImg = cat.images[imgIdx];
      let retIdx = (imgIdx + 1 + randInt(9)) % 10;
      returnImg = cat.images[retIdx];
      const conf = (0.45 + Math.random() * 0.20).toFixed(2);
      confidence = conf;
      badgeLabel = 'SUSPECT';
      badgeClasses = 'bg-warning/20 text-warning border-warning/30';
      pulseShadow = 'rgba(251,191,36,0.4)';
      // Moderate warm overlay — orange/yellow patches
      heatmapStyle = {
        background: `
          radial-gradient(ellipse at 35% 40%, rgba(251,191,36,0.5) 0%, transparent 50%),
          radial-gradient(ellipse at 65% 55%, rgba(250,204,21,0.45) 0%, transparent 45%),
          radial-gradient(ellipse at 50% 30%, rgba(251,191,36,0.3) 0%, transparent 55%),
          radial-gradient(ellipse at 45% 70%, rgba(251,146,60,0.35) 0%, transparent 40%)
        `,
      };
      break;
    }
    case 'fraud': {
      // Different categories entirely
      catalogImg = cat.images[imgIdx];
      const otherCatIdx = (catIdx + 1 + randInt(3)) % CATEGORIES.length;
      const otherCat = CATEGORIES[otherCatIdx];
      returnImg = otherCat.images[randInt(10)];
      const conf = (0.05 + Math.random() * 0.20).toFixed(2);
      confidence = conf;
      badgeLabel = 'FRAUD';
      badgeClasses = 'bg-danger/20 text-danger border-danger/30';
      pulseShadow = 'rgba(248,113,113,0.4)';
      // Intense red/hot overlay — dramatic bloom
      heatmapStyle = {
        background: `
          radial-gradient(ellipse at 30% 35%, rgba(248,113,113,0.6) 0%, transparent 50%),
          radial-gradient(ellipse at 70% 60%, rgba(239,68,68,0.55) 0%, transparent 45%),
          radial-gradient(ellipse at 50% 25%, rgba(248,113,113,0.45) 0%, transparent 55%),
          radial-gradient(ellipse at 40% 75%, rgba(220,38,38,0.5) 0%, transparent 40%),
          radial-gradient(ellipse at 60% 50%, rgba(251,146,60,0.35) 0%, transparent 55%)
        `,
      };
      break;
    }
  }

  return { catalogImg, returnImg, verdict: scenarioType, confidence, heatmapStyle, badgeLabel, badgeClasses, pulseShadow };
}

// --- Phase machine ---
type Phase = 'empty' | 'catalog' | 'return' | 'processing' | 'heatmap' | 'verdict';

const PHASE_DURATIONS: Record<Phase, number> = {
  empty: 1500,
  catalog: 2000,
  return: 2000,
  processing: 1800,
  heatmap: 2000,
  verdict: 2500,
};

const PHASE_ORDER: Phase[] = ['empty', 'catalog', 'return', 'processing', 'heatmap', 'verdict'];

export default function HeroVerification() {
  const [phase, setPhase] = useState<Phase>('empty');
  const [loopCount, setLoopCount] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Generate a new random scenario each loop
  const scenario = useMemo(() => generateScenario(), [loopCount]);

  const scheduleNext = useCallback((currentPhase: Phase) => {
    const idx = PHASE_ORDER.indexOf(currentPhase);
    if (idx === PHASE_ORDER.length - 1) {
      timerRef.current = setTimeout(() => {
        setLoopCount((n) => n + 1);
        setPhase('empty');
      }, 2000);
    } else {
      timerRef.current = setTimeout(() => {
        setPhase(PHASE_ORDER[idx + 1]);
      }, PHASE_DURATIONS[currentPhase]);
    }
  }, []);

  useEffect(() => {
    scheduleNext(phase);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [phase, loopCount, scheduleNext]);

  const phaseIdx = PHASE_ORDER.indexOf(phase);

  return (
    <>
      <style>{`
        @keyframes hv-pulse-border {
          0%, 100% { border-color: var(--color-border); }
          50% { border-color: var(--color-accent); opacity: 0.8; }
        }
        @keyframes hv-slide-up {
          from { opacity: 0; transform: translateY(24px) scale(0.96); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes hv-tag-in {
          from { opacity: 0; transform: scale(0.7); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes hv-scan-line {
          from { top: 0%; }
          to { top: 100%; }
        }
        @keyframes hv-pulse-text {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes hv-heatmap-bloom {
          from {
            opacity: 0;
            -webkit-mask-image: radial-gradient(circle at center, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 0%);
            mask-image: radial-gradient(circle at center, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 0%);
          }
          to {
            opacity: 1;
            -webkit-mask-image: radial-gradient(circle at center, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
            mask-image: radial-gradient(circle at center, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
          }
        }
        @keyframes hv-verdict-pop {
          0% { opacity: 0; transform: scale(0.5); }
          60% { transform: scale(1.15); }
          80% { transform: scale(0.95); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes hv-badge-pulse-genuine {
          0%, 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0.4); }
          50% { box-shadow: 0 0 0 8px rgba(74,222,128,0); }
        }
        @keyframes hv-badge-pulse-suspect {
          0%, 100% { box-shadow: 0 0 0 0 rgba(251,191,36,0.4); }
          50% { box-shadow: 0 0 0 8px rgba(251,191,36,0); }
        }
        @keyframes hv-badge-pulse-fraud {
          0%, 100% { box-shadow: 0 0 0 0 rgba(248,113,113,0.4); }
          50% { box-shadow: 0 0 0 8px rgba(248,113,113,0); }
        }

        .hv-container {
          font-family: var(--font-data), monospace;
        }
        .hv-empty-box {
          animation: hv-pulse-border 2s ease-in-out infinite;
        }
        .hv-img-enter {
          animation: hv-slide-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .hv-tag-enter {
          animation: hv-tag-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .hv-scan-line {
          animation: hv-scan-line 1.2s linear infinite;
        }
        .hv-analyzing {
          animation: hv-pulse-text 0.8s ease-in-out infinite;
        }
        .hv-heatmap {
          animation: hv-heatmap-bloom 2s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .hv-verdict {
          animation: hv-verdict-pop 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .hv-badge-pulse-genuine {
          animation: hv-badge-pulse-genuine 0.8s ease-in-out 2;
        }
        .hv-badge-pulse-suspect {
          animation: hv-badge-pulse-suspect 0.8s ease-in-out 2;
        }
        .hv-badge-pulse-fraud {
          animation: hv-badge-pulse-fraud 0.8s ease-in-out 2;
        }
      `}</style>

      <div className="hv-container rounded-xl border border-border bg-surface/50 p-4 sm:p-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3 sm:mb-4">
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span className="text-[10px] sm:text-xs text-muted" style={{ fontFamily: 'var(--font-data)' }}>
            LIVE VERIFICATION PREVIEW
          </span>
        </div>

        {/* Image panels */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          {/* Catalog panel */}
          <div className="relative rounded-lg bg-bg border border-border h-36 sm:h-44 overflow-hidden">
            {phaseIdx < 1 ? (
              <div className="hv-empty-box absolute inset-0 flex items-center justify-center border-2 border-dashed rounded-lg border-border">
                <span className="text-[10px] sm:text-xs text-muted">Catalog Image</span>
              </div>
            ) : (
              <div key={`catalog-${loopCount}`} className="hv-img-enter absolute inset-0">
                <img
                  src={scenario.catalogImg}
                  alt="Catalog"
                  className="w-full h-full object-cover"
                />
                {phase === 'processing' && (
                  <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="hv-scan-line absolute left-0 right-0 h-0.5 bg-accent/60" style={{ boxShadow: '0 0 12px 4px rgba(129,140,248,0.3)' }} />
                    <div className="absolute inset-0 bg-accent/5" />
                  </div>
                )}
                <div className="hv-tag-enter absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--color-success)]/20 text-[var(--color-success)] border border-[var(--color-success)]/30">
                  CATALOG
                </div>
              </div>
            )}
          </div>

          {/* Return / Heatmap panel */}
          <div className="relative rounded-lg bg-bg border border-border h-36 sm:h-44 overflow-hidden">
            {phaseIdx < 2 ? (
              <div className="hv-empty-box absolute inset-0 flex items-center justify-center border-2 border-dashed rounded-lg border-border">
                <span className="text-[10px] sm:text-xs text-muted">Return Image</span>
              </div>
            ) : phaseIdx < 4 ? (
              <div key={`return-${loopCount}`} className="hv-img-enter absolute inset-0">
                <img
                  src={scenario.returnImg}
                  alt="Return"
                  className="w-full h-full object-cover"
                />
                {phase === 'processing' && (
                  <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="hv-scan-line absolute left-0 right-0 h-0.5 bg-accent/60" style={{ boxShadow: '0 0 12px 4px rgba(129,140,248,0.3)' }} />
                    <div className="absolute inset-0 bg-accent/5" />
                  </div>
                )}
                <div className="hv-tag-enter absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--color-warning)]/20 text-[var(--color-warning)] border border-[var(--color-warning)]/30">
                  RETURN
                </div>
              </div>
            ) : (
              <div key={`heatmap-${loopCount}`} className="absolute inset-0">
                <img
                  src={scenario.returnImg}
                  alt="Return"
                  className="w-full h-full object-cover"
                />
                <div
                  className="hv-heatmap absolute inset-0"
                  style={scenario.heatmapStyle}
                />
                <div className="hv-tag-enter absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--color-danger)]/20 text-[var(--color-danger)] border border-[var(--color-danger)]/30">
                  DIFF MAP
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Analyzing text */}
        {phase === 'processing' && (
          <div className="flex justify-center mt-3 sm:mt-4">
            <span className="hv-analyzing text-xs sm:text-sm font-semibold text-accent" style={{ fontFamily: 'var(--font-data)' }}>
              ANALYZING...
            </span>
          </div>
        )}

        {/* Verdict badge */}
        {phase === 'verdict' && (
          <div key={`verdict-${loopCount}`} className="hv-verdict flex items-center justify-center gap-2 sm:gap-3 mt-3 sm:mt-4">
            <span className={`hv-badge-pulse-${scenario.verdict} inline-flex px-3 py-1 rounded-full text-xs font-semibold border ${scenario.badgeClasses}`}>
              {scenario.badgeLabel}
            </span>
            <span className="text-sm text-text" style={{ fontFamily: 'var(--font-data)' }}>{scenario.confidence}</span>
            <span className="text-[10px] sm:text-xs text-muted">confidence</span>
          </div>
        )}
      </div>
    </>
  );
}
