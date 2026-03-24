"use client";

import { useActionState } from "react";
import type { UserPreferences } from "@/types";
import { saveDigestPreferences } from "@/actions/preferences";

interface DigestPreferencesFormProps {
  preferences: UserPreferences;
}

export function DigestPreferencesForm({ preferences }: DigestPreferencesFormProps) {
  const [state, formAction, pending] = useActionState(saveDigestPreferences, undefined);

  return (
    <section className="rounded-xl border border-border bg-surface p-4 sm:p-5 mb-6">
      <h2 className="text-base font-semibold text-text-primary mb-3">Digest notifications</h2>
      <form action={formAction} className="space-y-4">
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            name="digest_enabled"
            defaultChecked={preferences.digest_enabled}
            className="h-4 w-4"
          />
          <span className="text-sm text-text-primary">Enable digest emails</span>
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm text-text-secondary">
            Frequency
            <select
              name="digest_frequency"
              defaultValue={preferences.digest_frequency}
              className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-text-primary"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </label>

          <label className="text-sm text-text-secondary">
            Delivery hour (UTC)
            <input
              type="number"
              min={0}
              max={23}
              name="digest_hour_utc"
              defaultValue={preferences.digest_hour_utc}
              className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-text-primary"
            />
          </label>
        </div>

        {state?.error && <p className="text-sm text-error">{state.error}</p>}

        <button
          type="submit"
          disabled={pending}
          className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50"
        >
          Save preferences
        </button>
      </form>
    </section>
  );
}
