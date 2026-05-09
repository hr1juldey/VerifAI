import { useEffect, useState } from 'react';

interface Props {
  text: string | null;
  attribution?: string;
  charDelay?: number;
  speedMultiplier?: number;
}

export default function TypewriterText({ text, attribution, charDelay = 60, speedMultiplier = 1 }: Props) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!text) {
      setDisplayed('');
      setDone(false);
      return;
    }

    setDisplayed('');
    setDone(false);
    let i = 0;
    const delay = charDelay * speedMultiplier;

    const timer = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(timer);
        setDone(true);
      }
    }, delay);

    return () => clearInterval(timer);
  }, [text, charDelay, speedMultiplier]);

  if (!text) {
    return <p className="text-sm text-muted italic">Explanation unavailable</p>;
  }

  return (
    <div className="space-y-2">
      {attribution && (
        <p className="text-xs font-data text-muted">{attribution}</p>
      )}
      <p className={`text-sm text-text leading-relaxed ${!done ? 'border-r-2 border-accent animate-pulse' : ''}`}>
        {displayed}
      </p>
    </div>
  );
}
