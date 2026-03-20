import type { Article } from "@/types";
import { ArticleCard } from "./article-card";

interface ArticleListProps {
  articles: Article[];
}

export function ArticleList({ articles }: ArticleListProps) {
  if (articles.length === 0) {
    return (
      <p className="text-center py-16 text-text-secondary text-lg">
        No articles available at the moment.
      </p>
    );
  }

  return (
    <div>
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
