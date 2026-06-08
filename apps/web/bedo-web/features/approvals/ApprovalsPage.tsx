"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, ClipboardCheck, PencilLine, X } from "lucide-react";
import { Button } from "@/components/Button";
import { trainerItemRoute } from "@/lib/route-ids";
import type { ApprovalRow } from "@/features/srs/types";
import { formatNodeId, formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";

type Props = {
  initialApprovals: ApprovalRow[];
};

export function ApprovalsPage({ initialApprovals }: Props) {
  const [approvals, setApprovals] = useState(initialApprovals);
  const [activeApproval, setActiveApproval] = useState<ApprovalRow | null>(null);
  const [error, setError] = useState("");

  async function refresh() {
    const response = await fetch("/api/approvals");
    if (response.ok) {
      const data = await response.json();
      setApprovals(data.approvals || []);
    }
  }

  async function approve(approval: ApprovalRow, payload?: Record<string, unknown>) {
    setError("");
    const response = await fetch(`/api/approvals/${approval.name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    if (!response.ok) {
      setError("Approval could not be completed. Check workflow state and permissions.");
      return;
    }
    setActiveApproval(null);
    await refresh();
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wide text-slate-500">
              <ClipboardCheck className="h-4 w-4" />
              Approval Center
            </div>
            <h2 className="mt-2 text-3xl font-black text-slate-950">Pending Approvals</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">Notifications create awareness. Approval decisions happen here.</p>
          </div>
        </div>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <div className="rounded-lg border border-slate-200 bg-white shadow-panel">
        <div className="border-b border-slate-200 px-5 py-4">
          <h3 className="text-lg font-black text-slate-950">Approval Queue</h3>
          <p className="text-sm font-medium text-slate-500">{approvals.length} item(s)</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-[1060px] w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-black uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Approval Type</th>
                <th className="px-4 py-3">Project</th>
                <th className="px-4 py-3">Trainer Item</th>
                <th className="px-4 py-3">Submitted By</th>
                <th className="px-4 py-3">Project Owner</th>
                <th className="px-4 py-3">Current Node</th>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Deadline</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {approvals.map((approval) => (
                <tr key={approval.name} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-black text-slate-950">{approval.approval_label}</td>
                  <td className="max-w-[220px] px-4 py-3">
                    <div className="font-bold text-slate-950">{approval.project_code}</div>
                    <div className="truncate text-xs text-slate-500">{approval.project_name}</div>
                  </td>
                  <td className="max-w-[180px] truncate px-4 py-3 font-semibold text-slate-700">{approval.trainer_item_name}</td>
                  <td className="px-4 py-3 text-slate-600">{approval.submitted_by_name || approval.submitted_by || "-"}</td>
                  <td className="px-4 py-3 text-slate-600">{approval.project_owner_name || "-"}</td>
                  <td className="px-4 py-3 text-slate-600">{formatNodeId(approval.current_node)}</td>
                  <td className="max-w-[180px] truncate px-4 py-3 text-slate-600">{approval.case_classification}</td>
                  <td className="px-4 py-3 font-semibold text-slate-700">{approval.deadline_proposal_days} day(s)</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-black ${statusBadgeClass(approval.status)}`}>{formatStatus(approval.status)}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-amber-50 px-2 py-1 text-xs font-black text-amber-800">{approval.priority}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Button className="min-h-9 px-3" type="button" onClick={() => approve(approval)}>
                        <CheckCircle2 className="h-4 w-4" />
                        Approve
                      </Button>
                      <Button className="min-h-9 px-3" variant="secondary" type="button" onClick={() => setActiveApproval(approval)}>
                        <PencilLine className="h-4 w-4" />
                        Edit
                      </Button>
                      <Link className="rounded-md border border-slate-200 px-3 py-2 text-xs font-black text-slate-700 hover:bg-slate-50" href={trainerItemRoute("srs", approval.project, approval.trainer_item)}>
                        Detail
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!approvals.length && <div className="m-5 rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">No pending approvals.</div>}
        </div>
      </div>

      {activeApproval && (
        <ApproveWithEditsModal
          approval={activeApproval}
          onClose={() => setActiveApproval(null)}
          onSubmit={(payload) => approve(activeApproval, payload)}
        />
      )}
    </section>
  );
}

function ApproveWithEditsModal({
  approval,
  onClose,
  onSubmit,
}: {
  approval: ApprovalRow;
  onClose: () => void;
  onSubmit: (payload: Record<string, unknown>) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <form
        className="w-full max-w-xl rounded-lg bg-white shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          onSubmit({
            with_edits: true,
            case_classification: form.get("case_classification"),
            deadline_proposal_days: Number(form.get("deadline_proposal_days") || 0),
            comments: form.get("comments"),
          });
        }}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">Approve With Edits</div>
            <h3 className="mt-1 text-xl font-black text-slate-950">{approval.approval_label}</h3>
          </div>
          <button className="rounded-md p-2 text-slate-500 hover:bg-slate-100" type="button" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4 px-6 py-5">
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
            <div className="font-black text-slate-950">{approval.project_code} | {approval.project_name}</div>
            <div className="mt-1 text-slate-600">{approval.trainer_item_name}</div>
          </div>
          <label className="block">
            <span className="text-sm font-black text-slate-800">Case Classification</span>
            <select className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="case_classification" defaultValue={approval.case_classification} required>
              <option>Case 1 - Legacy Validation</option>
              <option>Case 2 - Standard Innovation</option>
              <option>Case 3 - Experimental Prototyping</option>
              <option>Case 4 - Vanguard Manufacturing</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-black text-slate-800">Deadline Proposal</span>
            <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" min={1} step={1} name="deadline_proposal_days" type="number" defaultValue={approval.deadline_proposal_days || 1} required />
          </label>
          <label className="block">
            <span className="text-sm font-black text-slate-800">Comment</span>
            <textarea className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="comments" rows={3} />
          </label>
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit">Approve With Edits</Button>
        </div>
      </form>
    </div>
  );
}
