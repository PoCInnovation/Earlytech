export function formatRelativeDate(date: string): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "...";
}

export function formatPercentage(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function getScoreColor(score: number): string {
  const pct = score * 100;
  if (pct >= 90) return "text-[#16A34A]";
  if (pct >= 80) return "text-[#2563EB]";
  return "text-[#6B7280]";
}

export function getScoreBgColor(score: number): string {
  const pct = score * 100;
  if (pct >= 90) return "bg-green-50 text-[#16A34A]";
  if (pct >= 80) return "bg-blue-50 text-[#2563EB]";
  return "bg-gray-50 text-[#6B7280]";
}
