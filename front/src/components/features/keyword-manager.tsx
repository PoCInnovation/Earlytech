"use client";

import { useActionState, useOptimistic, startTransition } from "react";
import { Plus, X } from "lucide-react";
import type { UserKeyword } from "@/types";
import { addKeyword, deleteKeyword } from "@/actions/keywords";
import { Input } from "@/components/ui/input";

interface KeywordManagerProps {
  initialKeywords: UserKeyword[];
}

export function KeywordManager({ initialKeywords }: KeywordManagerProps) {
  const [optimisticKeywords, setOptimisticKeywords] = useOptimistic(initialKeywords);
  const [state, formAction, pending] = useActionState(addKeyword, undefined);

  function handleAdd(formData: FormData) {
    const keyword = (formData.get("keyword") as string)?.trim();
    if (!keyword) return;

    const tempKeyword: UserKeyword = {
      id: `temp-${Date.now()}`,
      user_id: "",
      keyword,
      created_at: new Date().toISOString(),
    };

    startTransition(() => {
      setOptimisticKeywords((prev) => [...prev, tempKeyword]);
      formAction(formData);
    });
  }

  function handleDelete(keywordId: string) {
    startTransition(() => {
      setOptimisticKeywords((prev) => prev.filter((k) => k.id !== keywordId));
      deleteKeyword(keywordId);
    });
  }

  return (
    <div>
      <form action={handleAdd} className="flex gap-2 mb-6">
        <div className="flex-1">
          <Input
            name="keyword"
            placeholder="Add a keyword..."
            disabled={pending}
            maxLength={100}
          />
        </div>
        <button
          type="submit"
          disabled={pending}
          className="px-4 py-3 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors disabled:opacity-50 flex items-center gap-1"
        >
          <Plus size={16} />
          <span className="hidden sm:inline">Add</span>
        </button>
      </form>

      {state?.error && (
        <p className="text-sm text-error mb-4">{state.error}</p>
      )}

      {optimisticKeywords.length === 0 ? (
        <p className="text-text-secondary text-sm py-8 text-center">
          No keywords yet. Add your first interest above.
        </p>
      ) : (
        <>
          <div className="border border-border rounded-lg divide-y divide-border">
            {optimisticKeywords.map((kw) => (
              <div key={kw.id} className="flex items-center justify-between px-4 py-3">
                <span className="text-sm text-text-primary">{kw.keyword}</span>
                <button
                  onClick={() => handleDelete(kw.id)}
                  className="p-1 text-text-muted hover:text-error transition-colors"
                  aria-label={`Remove ${kw.keyword}`}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
          <p className="text-xs text-text-muted mt-3">
            {optimisticKeywords.length} interest{optimisticKeywords.length !== 1 ? "s" : ""} configured
          </p>
        </>
      )}
    </div>
  );
}
