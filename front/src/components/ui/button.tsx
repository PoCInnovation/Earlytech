import { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed",
  secondary:
    "bg-transparent border border-border text-text-primary hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`px-6 py-3 rounded-lg font-medium text-sm transition-colors duration-150 ${variants[variant]} ${className}`}
      {...props}
    />
  );
}
