"use client";

import type { ReactNode } from "react";
import { Dialog } from "@/components/ui/Dialog";
import type { WorkflowActionDialogMeta } from "./workflow-types";

type WorkflowActionDialogProps = {
  meta: WorkflowActionDialogMeta;
  error?: string;
  onClose: () => void;
  children: ReactNode;
};

export function WorkflowActionDialog({ meta, error, onClose, children }: WorkflowActionDialogProps) {
  return (
    <Dialog
      eyebrow={meta.overline}
      title={meta.title}
      size="xl"
      onClose={onClose}
      context={
        <>
          <div className="grid gap-3 rounded-md border border-gray-200 bg-panel p-3 text-sm sm:grid-cols-3">
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
        </>
      }
    >
      {error && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</div>}
      {children}
    </Dialog>
  );
}
