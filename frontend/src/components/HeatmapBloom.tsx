import { useEffect, useRef, useState } from 'react';

interface Props {
  base64Image: string | null;
  bloomDuration?: number;
  speedMultiplier?: number;
}

export default function HeatmapBloom({ base64Image, bloomDuration = 2500, speedMultiplier = 1 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [bloomProgress, setBloomProgress] = useState(0);
  const [pulsing, setPulsing] = useState(false);
  const [useFallback, setUseFallback] = useState(false);

  // Check if mobile — use fallback
  useEffect(() => {
    setUseFallback(window.innerWidth < 768);
  }, []);

  // Bloom animation
  useEffect(() => {
    if (!base64Image || !canvasRef.current || useFallback) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;

      const duration = bloomDuration * speedMultiplier;
      const startTime = performance.now();

      const animate = (now: number) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        setBloomProgress(progress);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw the heatmap image
        ctx.drawImage(img, 0, 0);

        // Apply radial gradient mask — bloom from center
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const maxRadius = Math.sqrt(cx * cx + cy * cy);
        const currentRadius = maxRadius * progress;

        // Mask: hide everything outside the bloom radius
        ctx.globalCompositeOperation = 'destination-in';
        const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, currentRadius);
        gradient.addColorStop(0, 'rgba(255,255,255,1)');
        gradient.addColorStop(0.7, 'rgba(255,255,255,0.9)');
        gradient.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.globalCompositeOperation = 'source-over';

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setPulsing(true);
          // Stop pulsing after 3 seconds
          setTimeout(() => setPulsing(false), 3000);
        }
      };

      requestAnimationFrame(animate);
    };
    img.src = `data:image/png;base64,${base64Image}`;
  }, [base64Image, bloomDuration, speedMultiplier, useFallback]);

  // Fallback: static image on mobile
  if (!base64Image) return null;

  if (useFallback) {
    return (
      <div className="rounded-lg overflow-hidden border border-border">
        <img
          src={`data:image/png;base64,${base64Image}`}
          alt="Spatial diff heatmap"
          className="w-full h-auto"
        />
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden border border-border">
      <canvas
        ref={canvasRef}
        className={`w-full h-auto ${pulsing ? 'animate-[glow-pulse_2s_ease-in-out_infinite]' : ''}`}
        style={{
          filter: pulsing ? 'brightness(1.1)' : 'none',
          transition: 'filter 0.5s ease-in-out',
        }}
      />
      {bloomProgress < 1 && (
        <div className="absolute bottom-2 right-2 bg-bg/80 backdrop-blur-sm rounded px-2 py-0.5">
          <span className="text-xs font-data text-accent">{Math.round(bloomProgress * 100)}%</span>
        </div>
      )}
    </div>
  );
}
