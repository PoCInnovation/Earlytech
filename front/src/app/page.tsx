import { getArticles } from "@/actions/articles";
import { SourceFilter } from "@/components/features/source-filter";

export default async function HomePage() {
  const data = await getArticles();
  const articles = data?.articles ?? [];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-10">
        <h1 className="font-serif text-4xl font-bold text-text-primary mb-2">
          Tech, filtered for you.
        </h1>
        <p className="text-text-secondary text-lg">5 sources, zero noise.</p>
      </div>

      <SourceFilter articles={articles} />
    </div>
  );
}
