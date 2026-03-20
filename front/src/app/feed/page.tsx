import { getSession } from "@/lib/auth";
import { getUserFeed, getUserStats } from "@/actions/articles";
import { ArticleCardFeed } from "@/components/features/article-card-feed";
import { EmptyState } from "@/components/ui/empty-state";
import { formatPercentage } from "@/lib/utils";

export default async function FeedPage() {
  const session = await getSession();
  if (!session) return null;

  const [feed, stats] = await Promise.all([
    getUserFeed(session.userId),
    getUserStats(session.userId),
  ]);

  const articles = feed?.articles ?? [];

  if (stats && stats.total_keywords === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
        <EmptyState
          message="Start by adding your interests"
          actionLabel="Go to settings"
          actionHref="/settings"
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-10">
        <h1 className="font-serif text-3xl font-bold text-text-primary mb-2">
          Your news feed
        </h1>
        {stats && (
          <p className="text-text-secondary text-sm">
            {stats.total_articles} matched articles
            {stats.avg_similarity > 0 && (
              <span className="ml-2 pl-2 border-l border-border">
                Avg similarity: {formatPercentage(stats.avg_similarity)}
              </span>
            )}
          </p>
        )}
      </div>

      {articles.length === 0 ? (
        <EmptyState message="No articles match your interests yet. The scraper runs continuously, check back soon!" />
      ) : (
        <div>
          {articles.map((article) => (
            <ArticleCardFeed key={`${article.id}-${article.matched_keyword}`} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
