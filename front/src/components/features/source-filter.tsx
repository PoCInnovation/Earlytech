"use client";

import { useState } from "react";
import type { Article, SourceType } from "@/types";
import { SOURCES, ALL_SOURCES } from "@/lib/sources";
import { ArticleList } from "./article-list";

interface SourceFilterProps {
  articles: Article[];
}

export function SourceFilter({ articles }: SourceFilterProps) {
  const [activeSources, setActiveSources] = useState<Set<SourceType>>(new Set(ALL_SOURCES));

  function toggleSource(source: SourceType) {
    setActiveSources((prev) => {
      const next = new Set(prev);
      if (next.has(source)) {
        if (next.size === 1) return prev;
        next.delete(source);
      } else {
        next.add(source);
      }
      return next;
    });
  }

  const filtered = articles.filter((a) => activeSources.has(a.source as SourceType));

  return (
    <>
      <div className="flex flex-wrap gap-2 mb-8">
        {ALL_SOURCES.map((source) => {
          const config = SOURCES[source];
          const active = activeSources.has(source);
          return (
            <button
              key={source}
              onClick={() => toggleSource(source)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                active ? config.color : "bg-gray-100 text-text-muted"
              }`}
            >
              {config.label}
            </button>
          );
        })}
      </div>
      <ArticleList articles={filtered} />
    </>
  );
}
