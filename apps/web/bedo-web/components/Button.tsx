import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition",
        variant === "primary" && "bg-ink text-white hover:bg-steel",
        variant === "secondary" && "border border-gray-300 bg-white text-ink hover:bg-gray-50",
        variant === "danger" && "bg-red-700 text-white hover:bg-red-800",
        className
      )}
      {...props}
    />
  );
}
