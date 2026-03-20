import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api-client";
import { SourceBadge } from "@/components/ui/badge";
import { ArrowLeft, ExternalLink } from "lucide-react";

interface ArticlePageProps {
  params: Promise<{ id: string }>;
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params;

  let article;
  try {
    article = await api.getArticle(id);
  } catch {
    notFound();
  }

  const publishedDate = article.published_date
    ? new Date(article.published_date).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary mb-8 transition-colors"
      >
        <ArrowLeft size={16} />
        Back
      </Link>

      <div className="flex items-center gap-3 mb-4">
        <SourceBadge source={article.source} />
        {publishedDate && (
          <span className="text-sm text-text-muted">{publishedDate}</span>
        )}
      </div>

      {article.title && (
        <h1 className="font-serif text-3xl font-bold text-text-primary leading-tight mb-4">
          {article.title}
        </h1>
      )}

      {article.authors && article.authors.length > 0 && (
        <p className="text-sm text-text-secondary mb-8">
          By {article.authors.join(", ")}
        </p>
      )}

      <hr className="border-border mb-8" />

      {article.content ? (
        <div className="prose prose-gray max-w-none text-text-primary leading-relaxed whitespace-pre-line">
          {article.content}
        </div>
      ) : article.summary ? (
        <p className="text-text-secondary leading-relaxed">{article.summary}</p>
      ) : (
        <p className="text-text-muted">No content available.</p>
      )}

      <hr className="border-border my-8" />

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 text-sm font-medium text-text-primary hover:text-accent-hover transition-colors"
      >
        View on original source
        <ExternalLink size={14} />
      </a>
    </div>
  );
}
