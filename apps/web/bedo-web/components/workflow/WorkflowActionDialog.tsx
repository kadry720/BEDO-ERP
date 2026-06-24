"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import type { WorkflowActionDialogMeta } from "./workflow-types";

type WorkflowActionDialogProps = {
  meta: WorkflowActionDialogMeta;
  error?: string;
  onClose: () => void;
  children: ReactNode;
};

export function WorkflowActionDialog({ meta, error, onClose, children }: WorkflowActionDialogProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    previouslyFocused.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused.current?.focus();
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4">
      <div
        className="flex max-h-[92vh] w-full max-w-3xl flex-col rounded-md bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="workflow-dialog-title"
      >
        <div className="border-b border-gray-200 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs font-bold uppercase text-muted">{meta.overline}</div>
              <h3 id="workflow-dialog-title" className="mt-1 text-xl font-bold text-ink">{meta.title}</h3>
            </div>
            <button ref={closeRef} className="focus-ring rounded-md p-2 hover:bg-gray-100" type="button" onClick={onClose} aria-label="Close">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="mt-4 grid gap-3 rounded-md border border-gray-200 bg-panel p-3 text-sm sm:grid-cols-3">
            <div>
              <div className="text-xs font-bold uppercase text-muted">Project</div>
              <div className="mt-1 font-semibold text-ink">{meta.projectCode}</div>
            </div>
            <div>
              <div className="text-xs font-bold uppercase text-muted">Trainer Item</div>
              <div className="mt-1 font-semibold text-ink">{meta.trainerItem}</div>
            </div>
            <div>
              <div className="text-xs font-bold uppercase text-muted">Status</div>
              <div className="mt-1">{meta.status}</div>
            </div>
          </div>
          {meta.deadline && <div className="mt-3">{meta.deadline}</div>}
        </div>
        <div className="min-h-0 overflow-y-auto px-6 py-5">
          {error && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</div>}
          {children}
        </div>
      </div>
    </div>
  );
}
