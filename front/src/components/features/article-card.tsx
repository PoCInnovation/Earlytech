import type { Article } from "@/types";
import { SourceBadge } from "@/components/ui/badge";
import { formatRelativeDate, truncate } from "@/lib/utils";

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const displaySummary = article.summary || (article.content ? truncate(article.content, 150) : null);
  const dateStr = article.published_date || article.scraped_at;

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block py-6 border-b border-border hover:bg-gray-50/50 transition-colors -mx-4 px-4 sm:-mx-6 sm:px-6"
    >
      <div className="flex items-center gap-3 mb-2">
        <SourceBadge source={article.source} />
        <span className="text-xs text-text-muted">{formatRelativeDate(dateStr)}</span>
      </div>

      {article.title && (
        <h2 className="font-serif text-xl font-semibold leading-tight text-text-primary line-clamp-2 mb-1">
          {article.title}
        </h2>
      )}

      {displaySummary && (
        <p className="text-sm text-text-secondary leading-relaxed line-clamp-2 mb-2">
          {displaySummary}
        </p>
      )}

      {article.authors && article.authors.length > 0 && (
        <p className="text-xs text-text-muted">
          By {article.authors.join(", ")}
        </p>
      )}
    </a>
  );
}
