import { useCallback, useRef, useState, type DragEvent } from 'react';

interface Props {
  label: string;
  onFileSelect: (file: File) => void;
  onFileClear: () => void;
  file?: File | null;
}

const ALLOWED = ['image/png', 'image/jpeg', 'image/jpg'];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function ImageUpload({ label, onFileSelect, onFileClear, file }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback((f: File): string | null => {
    if (!ALLOWED.includes(f.type)) return 'Please select an image file (PNG, JPG, JPEG)';
    if (f.size > MAX_SIZE) return 'Image must be smaller than 10MB';
    return null;
  }, []);

  const handleFile = useCallback(
    (f: File) => {
      const err = validate(f);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      setPreview(URL.createObjectURL(f));
      onFileSelect(f);
    },
    [validate, onFileSelect],
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback(() => setDragging(false), []);

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const clear = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
    onFileClear();
  }, [preview, onFileClear]);

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-muted">{label}</label>

      {preview ? (
        <div className="relative rounded-lg overflow-hidden border border-border bg-surface">
          <img src={preview} alt="Preview" className="w-full h-48 object-contain" />
          <button
            onClick={clear}
            className="absolute top-2 right-2 bg-bg/80 text-muted hover:text-text rounded-full w-7 h-7 flex items-center justify-center text-sm backdrop-blur-sm transition-colors"
            aria-label="Clear image"
          >
            ✕
          </button>
          {file && <p className="text-xs text-muted px-3 pb-2 truncate">{file.name}</p>}
        </div>
      ) : (
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`
            flex flex-col items-center justify-center gap-2 h-48 rounded-lg border-2 border-dashed cursor-pointer transition-colors
            ${dragging ? 'border-accent bg-accent/5' : 'border-border hover:border-muted bg-surface'}
          `}
        >
          <svg className="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
          </svg>
          <p className="text-sm text-muted">Drop image or click to browse</p>
          <p className="text-xs text-muted/60">PNG, JPG, JPEG · Max 10MB</p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept=".png,.jpg,.jpeg"
        onChange={onInputChange}
        className="hidden"
      />

      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}
