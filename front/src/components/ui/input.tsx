import { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export function Input({ error, className = "", ...props }: InputProps) {
  return (
    <div className="w-full">
      <input
        className={`w-full px-4 py-3 border rounded-lg text-base bg-surface text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none transition-colors ${
          error ? "border-error" : "border-border"
        } ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-error">{error}</p>}
    </div>
  );
}
