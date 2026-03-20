import Link from "next/link";

interface EmptyStateProps {
  message: string;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({ message, actionLabel, actionHref }: EmptyStateProps) {
  return (
    <div className="text-center py-16">
      <p className="text-text-secondary text-lg">{message}</p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="inline-block mt-4 px-6 py-3 bg-accent text-white rounded-lg font-medium text-sm hover:bg-accent-hover transition-colors"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
