import { ArticleSkeleton } from "@/components/ui/skeleton";
import { Skeleton } from "@/components/ui/skeleton";

export default function FeedLoading() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <Skeleton className="h-9 w-48 mb-2" />
      <Skeleton className="h-5 w-64 mb-10" />
      {Array.from({ length: 4 }).map((_, i) => (
        <ArticleSkeleton key={i} />
      ))}
    </div>
  );
}
