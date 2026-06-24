import Link from "next/link";
import { clsx } from "clsx";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg" | "icon";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

type LinkButtonProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  href: string;
  variant?: ButtonVariant;
  size?: Exclude<ButtonSize, "icon">;
  children: ReactNode;
};

const baseClass = "focus-ring inline-flex items-center justify-center gap-2 rounded-md font-black transition disabled:cursor-not-allowed disabled:opacity-60";

const variantClass: Record<ButtonVariant, string> = {
  primary: "bg-ink text-white hover:bg-steel",
  secondary: "border border-slate-300 bg-white text-ink hover:bg-slate-50",
  danger: "bg-red-700 text-white hover:bg-red-800",
  ghost: "text-slate-700 hover:bg-slate-100",
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 text-xs",
  md: "min-h-10 px-4 text-sm",
  lg: "min-h-12 px-5 text-base",
  icon: "h-10 w-10 p-0",
};

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  return <button className={clsx(baseClass, variantClass[variant], sizeClass[size], className)} {...props} />;
}

export function IconButton({ className, variant = "secondary", ...props }: ButtonProps) {
  return <Button className={className} variant={variant} size="icon" {...props} />;
}

export function LinkButton({ className, variant = "primary", size = "md", href, children, ...props }: LinkButtonProps) {
  return (
    <Link className={clsx(baseClass, variantClass[variant], sizeClass[size], className)} href={href} {...props}>
      {children}
    </Link>
  );
}
