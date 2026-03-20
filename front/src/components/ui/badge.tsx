import { SOURCES } from "@/lib/sources";
import type { SourceType } from "@/types";
import { formatPercentage, getScoreBgColor } from "@/lib/utils";

interface SourceBadgeProps {
  source: string;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  const config = SOURCES[source as SourceType];
  if (!config) return <span className="text-xs text-text-secondary">{source}</span>;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  );
}

interface ScoreBadgeProps {
  score: number;
}

export function ScoreBadge({ score }: ScoreBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold font-mono ${getScoreBgColor(score)}`}
    >
      {formatPercentage(score)}
    </span>
  );
}
