"use client";

import { useActionState, useState, useTransition } from "react";
import type { UserExcludedKeyword } from "@/types";
import { ALL_SOURCES, SOURCES } from "@/lib/sources";
import { addExcludedKeyword, addExcludedSource, deleteExcludedKeyword, deleteExcludedSource } from "@/actions/preferences";

interface ExclusionsManagerProps {
  excludedSources: string[];
  excludedKeywords: UserExcludedKeyword[];
}

export function ExclusionsManager({ excludedSources, excludedKeywords }: ExclusionsManagerProps) {
  const [sources, setSources] = useState(new Set(excludedSources));
  const [keywords, setKeywords] = useState(excludedKeywords);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [pendingSource, startSourceTransition] = useTransition();
  const [state, formAction, pendingKeyword] = useActionState(addExcludedKeyword, undefined);

  function toggleSource(source: string) {
    setSourceError(null);
    startSourceTransition(async () => {
      if (sources.has(source)) {
        const res = await deleteExcludedSource(source);
        if (res.error) {
          setSourceError(res.error);
          return;
        }
        setSources((prev) => {
          const next = new Set(prev);
          next.delete(source);
          return next;
        });
        return;
      }

      const res = await addExcludedSource(source);
      if (res.error) {
        setSourceError(res.error);
        return;
      }
      setSources((prev) => new Set([...prev, source]));
    });
  }

  async function handleDeleteKeyword(keywordId: string) {
    const res = await deleteExcludedKeyword(keywordId);
    if (res.error) return;
    setKeywords((prev) => prev.filter((k) => k.id !== keywordId));
  }

  function handleAddKeyword(formData: FormData) {
    const raw = (formData.get("keyword") as string | null)?.trim();
    if (!raw) return;
    formAction(formData);
  }

  return (
    <section className="rounded-xl border border-border bg-surface p-4 sm:p-5">
      <h2 className="text-base font-semibold text-text-primary mb-3">Exclusions</h2>

      <p className="text-sm text-text-secondary mb-2">Ignore specific sources</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {ALL_SOURCES.map((source) => {
          const selected = sources.has(source);
          return (
            <button
              key={source}
              type="button"
              onClick={() => toggleSource(source)}
              disabled={pendingSource}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                selected
                  ? "bg-red-50 text-red-700 border-red-200"
                  : `${SOURCES[source].color} border-transparent`
              }`}
            >
              {selected ? `Excluded: ${SOURCES[source].label}` : SOURCES[source].label}
            </button>
          );
        })}
      </div>

      {sourceError && <p className="text-sm text-error mb-3">{sourceError}</p>}

      <p className="text-sm text-text-secondary mb-2">Ignore articles matching these keywords</p>
      <form action={handleAddKeyword} className="flex gap-2 mb-3">
        <input
          name="keyword"
          placeholder="Add excluded keyword..."
          maxLength={100}
          className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm"
          disabled={pendingKeyword}
        />
        <button
          type="submit"
          disabled={pendingKeyword}
          className="px-3 py-2 rounded-lg bg-accent text-white text-sm disabled:opacity-50"
        >
          Add
        </button>
      </form>

      {state?.error && <p className="text-sm text-error mb-3">{state.error}</p>}

      {keywords.length === 0 ? (
        <p className="text-sm text-text-muted">No excluded keywords.</p>
      ) : (
        <div className="space-y-2">
          {keywords.map((kw) => (
            <div key={kw.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
              <span className="text-sm text-text-primary">{kw.keyword}</span>
              <button
                type="button"
                onClick={() => handleDeleteKeyword(kw.id)}
                className="text-xs text-text-secondary hover:text-error"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
