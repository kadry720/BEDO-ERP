import { clsx } from "clsx";

export type SegmentOption = {
  value: string;
  label: string;
  count?: number;
};

export function SegmentedControl({ label, options, value, onChange }: { label: string; options: SegmentOption[]; value: string; onChange: (value: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label={label}>
      {options.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={clsx(
              "focus-ring inline-flex min-h-9 items-center gap-2 rounded-md border px-3 py-2 text-sm font-black",
              active ? "border-slate-950 bg-slate-950 text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
            )}
            onClick={() => onChange(option.value)}
          >
            <span>{option.label}</span>
            {option.count !== undefined && (
              <span className={clsx("rounded px-1.5 py-0.5 text-[11px]", active ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600")}>{option.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
