import { useEffect, useState } from 'react';

interface Props {
  message: string | null;
  onDismiss: () => void;
}

export default function ErrorToast({ message, onDismiss }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!message) {
      setVisible(false);
      return;
    }
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [message, onDismiss]);

  if (!message) return null;

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-md transition-all duration-300 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
      }`}
    >
      <div className="flex items-start gap-3 bg-surface border border-danger/30 rounded-lg px-4 py-3 shadow-lg shadow-danger/5">
        <svg className="w-5 h-5 text-danger shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm text-text">{message}</p>
        <button
          onClick={() => { setVisible(false); setTimeout(onDismiss, 300); }}
          className="text-muted hover:text-text shrink-0 ml-2"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
