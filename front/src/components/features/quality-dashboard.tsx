import type { UserQualityStats } from "@/types";
import { formatPercentage } from "@/lib/utils";

interface QualityDashboardProps {
  quality: UserQualityStats;
}

function formatRate(rate: number): string {
  return `${Math.round(rate)}%`;
}

export function QualityDashboard({ quality }: QualityDashboardProps) {
  return (
    <section className="mb-8 rounded-xl border border-border bg-surface p-4 sm:p-5">
      <h2 className="text-base font-semibold text-text-primary mb-3">Recommendation quality</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-text-muted">Relevant rate</p>
          <p className="text-lg font-semibold text-text-primary">{formatRate(quality.relevance_rate)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-text-muted">Feedback coverage</p>
          <p className="text-lg font-semibold text-text-primary">{formatRate(quality.feedback_coverage_rate)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-text-muted">Avg similarity</p>
          <p className="text-lg font-semibold text-text-primary">{formatPercentage(quality.avg_similarity)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3">
          <p className="text-xs text-text-muted">Feedback count</p>
          <p className="text-lg font-semibold text-text-primary">{quality.total_feedback}</p>
        </div>
      </div>
    </section>
  );
}
