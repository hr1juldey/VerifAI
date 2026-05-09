interface Props {
  decision: 'MATCH' | 'SUSPECT' | 'REJECT';
}

const styles: Record<string, string> = {
  MATCH: 'bg-success/20 text-success border-success/30',
  SUSPECT: 'bg-warning/20 text-warning border-warning/30',
  REJECT: 'bg-danger/20 text-danger border-danger/30',
};

export default function StatusBadge({ decision }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold tracking-wide border ${styles[decision]}`}
    >
      <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
      {decision}
    </span>
  );
}
