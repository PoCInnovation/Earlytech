import type { ArticleWithDelivery } from "@/types";
import { SourceBadge, ScoreBadge } from "@/components/ui/badge";
import { formatRelativeDate } from "@/lib/utils";
import { FeedbackButtons } from "@/components/features/feedback-buttons";

interface ArticleCardFeedProps {
  article: ArticleWithDelivery;
}

export function ArticleCardFeed({ article }: ArticleCardFeedProps) {
  const dateStr = article.published_date || article.delivered_at;

  return (
    <div className="py-6 border-b border-border -mx-4 px-4 sm:-mx-6 sm:px-6">
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block hover:bg-gray-50/50 transition-colors -mx-2 px-2 rounded-md"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <SourceBadge source={article.source} />
            <span className="text-xs text-text-muted">{formatRelativeDate(dateStr)}</span>
          </div>
          <ScoreBadge score={article.similarity_score} />
        </div>

        {article.title && (
          <h2 className="font-serif text-xl font-semibold leading-tight text-text-primary line-clamp-2 mb-1">
            {article.title}
          </h2>
        )}

        {article.summary && (
          <p className="text-sm text-text-secondary leading-relaxed line-clamp-2 mb-2">
            {article.summary}
          </p>
        )}
      </a>

      <p className="text-xs text-text-muted">
        Recommended because it matches your interest: &quot;{article.matched_keyword}&quot;
      </p>

      <FeedbackButtons articleId={article.id} currentFeedback={article.feedback} />
    </div>
  );
}
