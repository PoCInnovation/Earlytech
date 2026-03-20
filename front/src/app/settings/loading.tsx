import { Skeleton } from "@/components/ui/skeleton";

export default function SettingsLoading() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <Skeleton className="h-9 w-48 mb-2" />
      <Skeleton className="h-5 w-96 mb-8" />
      <div className="flex gap-2 mb-6">
        <Skeleton className="h-12 flex-1 rounded-lg" />
        <Skeleton className="h-12 w-20 rounded-lg" />
      </div>
      <div className="border border-border rounded-lg divide-y divide-border">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="px-4 py-3">
            <Skeleton className="h-5 w-40" />
          </div>
        ))}
      </div>
    </div>
  );
}
