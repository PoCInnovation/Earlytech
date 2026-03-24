"use client";

import { useState, useTransition } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { submitArticleFeedback } from "@/actions/feedback";

interface FeedbackButtonsProps {
  articleId: string;
  currentFeedback?: "relevant" | "not_relevant" | null;
}

export function FeedbackButtons({ articleId, currentFeedback }: FeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<"relevant" | "not_relevant" | null>(currentFeedback ?? null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleFeedback(nextFeedback: "relevant" | "not_relevant") {
    setError(null);
    startTransition(async () => {
      const result = await submitArticleFeedback(articleId, nextFeedback);
      if (result.error) {
        setError(result.error);
        return;
      }
      setFeedback(nextFeedback);
    });
  }

  return (
    <div className="mt-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => handleFeedback("relevant")}
          disabled={isPending}
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${
            feedback === "relevant"
              ? "bg-green-50 text-green-700"
              : "bg-gray-100 text-text-secondary hover:bg-gray-200"
          }`}
        >
          <ThumbsUp size={14} />
          Useful
        </button>
        <button
          type="button"
          onClick={() => handleFeedback("not_relevant")}
          disabled={isPending}
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${
            feedback === "not_relevant"
              ? "bg-red-50 text-red-700"
              : "bg-gray-100 text-text-secondary hover:bg-gray-200"
          }`}
        >
          <ThumbsDown size={14} />
          Not relevant
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-error">{error}</p>}
    </div>
  );
}
