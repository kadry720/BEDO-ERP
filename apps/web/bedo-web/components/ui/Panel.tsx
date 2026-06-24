import { clsx } from "clsx";
import type { HTMLAttributes, ReactNode } from "react";

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("rounded-md border border-slate-200 bg-white shadow-panel", className)} {...props} />;
}

export function PanelHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("border-b border-slate-200 px-5 py-4", className)} {...props} />;
}

export function PanelBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("px-5 py-5", className)} {...props} />;
}

export function EmptyState({ title, description, className }: { title: string; description?: string; className?: string }) {
  return (
    <div className={clsx("rounded-md border border-dashed border-slate-300 bg-white p-8 text-center", className)}>
      <div className="text-sm font-black text-slate-700">{title}</div>
      {description && <p className="mt-1 text-sm font-semibold text-slate-500">{description}</p>}
    </div>
  );
}

export function PageToolbar({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("flex flex-wrap items-end gap-3", className)}>{children}</div>;
}
