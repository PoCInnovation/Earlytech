import { getSession } from "@/lib/auth";
import { api } from "@/lib/api-client";
import { DigestPreferencesForm } from "@/components/features/digest-preferences-form";
import { ExclusionsManager } from "@/components/features/exclusions-manager";
import { KeywordManager } from "@/components/features/keyword-manager";
import type { UserExclusionResponse, UserKeyword, UserPreferences } from "@/types";

export default async function SettingsPage() {
  const session = await getSession();
  if (!session) return null;

  let keywords: UserKeyword[] = [];
  let preferences: UserPreferences | null = null;
  let exclusions: UserExclusionResponse = { sources: [], keywords: [] };
  try {
    const [kw, prefs, ex] = await Promise.all([
      api.getUserKeywords(session.userId),
      api.getUserPreferences(session.userId),
      api.getUserExclusions(session.userId),
    ]);
    keywords = kw;
    preferences = prefs;
    exclusions = ex;
  } catch {
    keywords = [];
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-text-primary mb-2">
          Your interests
        </h1>
        <p className="text-text-secondary text-sm">
          Articles are matched semantically: &quot;GPT-3&quot;, &quot;GPT 3&quot; and &quot;GPT3&quot; all give the same results.
        </p>
      </div>

      <KeywordManager initialKeywords={keywords} />

      {preferences && <DigestPreferencesForm preferences={preferences} />}

      <ExclusionsManager
        excludedSources={exclusions.sources}
        excludedKeywords={exclusions.keywords}
      />
    </div>
  );
}
