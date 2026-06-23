"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, ClipboardCheck, PencilLine, Search, X } from "lucide-react";
import { Button } from "@/components/Button";
import { COMMAND_CENTER_CASE_3, commandCenterDecisionRequiresDeadline } from "@/features/srs/commandCenterRules";
import type { ApprovalRow } from "@/features/srs/types";
import { formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";

type Props = {
  initialApprovals: ApprovalRow[];
};

const srsCaseOptions = [
  "Case 1 - Legacy Validation",
  "Case 2 - Standard Innovation",
  "Case 3 - Experimental Prototyping",
  "Case 4 - Vanguard Manufacturing",
];

const commandCenterCaseOptions = [
  "Case 1 - Save for later",
  "Case 2 - Buy Critical Components then deliver to ARD",
  "Case 3 - Deliver to ARD directly",
];

const approvalDepartmentOrder = ["SRS", "ARD", "Command Center", "Suppliers"];

export function ApprovalsPage({ initialApprovals }: Props) {
  const [approvals, setApprovals] = useState(initialApprovals);
  const [activeApproval, setActiveApproval] = useState<ApprovalRow | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");

  const departmentTabs = useMemo(() => approvalDepartmentTabs(approvals), [approvals]);
  const approvalTypes = useMemo(() => uniqueSorted(approvals.map((approval) => approval.approval_label)), [approvals]);
  const priorities = useMemo(() => uniqueSorted(approvals.map((approval) => approval.priority)), [approvals]);
  const visibleApprovals = useMemo(
    () => filterAndSortApprovals(approvals, { search, departmentFilter, typeFilter, priorityFilter, sortBy }),
    [approvals, search, departmentFilter, typeFilter, priorityFilter, sortBy]
  );

  async function refresh() {
    const response = await fetch("/api/approvals");
    if (response.ok) {
      const data = await response.json();
      setApprovals(data.approvals || []);
      window.dispatchEvent(new Event("bedo:approvals-changed"));
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
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-black text-slate-950">Approval Queue</h3>
              <p className="text-sm font-medium text-slate-500">{visibleApprovals.length} of {approvals.length} item(s)</p>
            </div>
            <Button
              className="min-h-9 px-3"
              variant="secondary"
              type="button"
              onClick={() => {
                setSearch("");
                setDepartmentFilter("all");
                setTypeFilter("all");
                setPriorityFilter("all");
                setSortBy("newest");
              }}
            >
              Reset
            </Button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2" role="tablist" aria-label="Approval source">
            {departmentTabs.map((tab) => {
              const active = departmentFilter === tab.value;
              return (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={`focus-ring inline-flex min-h-9 items-center gap-2 rounded-md border px-3 py-2 text-sm font-black ${
                    active
                      ? "border-slate-950 bg-slate-950 text-white"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                  onClick={() => setDepartmentFilter(tab.value)}
                >
                  <span>{tab.label}</span>
                  <span className={`rounded px-1.5 py-0.5 text-[11px] ${active ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600"}`}>
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="mt-4 grid items-end gap-3 lg:grid-cols-[minmax(260px,1fr)_220px_180px_220px]">
            <label className="flex h-full flex-col justify-end">
              <span className="min-h-5 text-xs font-black uppercase tracking-wide text-slate-500">Search</span>
              <span className="focus-within:focus-ring mt-2 flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3">
                <Search className="h-4 w-4 text-slate-400" />
                <input
                  className="w-full border-0 bg-transparent py-2 text-sm font-semibold text-slate-800 outline-none placeholder:text-slate-400"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Project, trainer, owner, case..."
                />
              </span>
            </label>
            <FilterSelect label="Approval type" value={typeFilter} onChange={setTypeFilter} options={approvalTypes} />
            <FilterSelect label="Priority" value={priorityFilter} onChange={setPriorityFilter} options={priorities} />
            <label className="flex h-full flex-col justify-end">
              <span className="min-h-5 text-xs font-black uppercase tracking-wide text-slate-500">Sort By</span>
              <select className="focus-ring mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="priority">Priority first</option>
                <option value="deadline_desc">Longest deadline</option>
                <option value="deadline_asc">Shortest deadline</option>
                <option value="project">Project code</option>
              </select>
            </label>
          </div>
        </div>

        <div className="grid gap-4 p-5">
          {visibleApprovals.map((approval) => (
            <ApprovalCard
              key={approval.name}
              approval={approval}
              onApprove={(payload) => (isGlobalDeadlineExtensionApproval(approval) ? setActiveApproval(approval) : approve(approval, payload))}
              onDeny={() => approve(approval, { action: "deny" })}
              onEdit={() => setActiveApproval(approval)}
            />
          ))}
          {!approvals.length && <EmptyApprovals message="No pending approvals." />}
          {Boolean(approvals.length) && !visibleApprovals.length && <EmptyApprovals message="No approvals match the current filters." />}
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

function ApprovalCard({ approval, onApprove, onDeny, onEdit }: { approval: ApprovalRow; onApprove: (payload?: Record<string, unknown>) => void; onDeny: () => void; onEdit: () => void }) {
  const globalExtension = isGlobalDeadlineExtensionApproval(approval);
  const supplierExtension = isSupplierExtensionApproval(approval);
  const handoverFailure = isHandoverFailureApproval(approval);
  const canDeny = isPmdpDualGateApproval(approval) || supplierExtension;
  const canEdit = !canDeny && !globalExtension && !handoverFailure;
  return (
    <article className="rounded-lg border border-slate-200 bg-white shadow-sm transition hover:border-slate-300">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-black uppercase tracking-wide text-slate-600">{approval.approval_label}</span>
            <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-black ${statusBadgeClass(approval.status)}`}>{formatStatus(approval.status)}</span>
            <span className={priorityClass(approval.priority)}>{approval.priority}</span>
            <span className="rounded bg-sky-50 px-2.5 py-1 text-xs font-black text-sky-800">{approvalDepartment(approval)}</span>
          </div>
          <h4 className="mt-3 break-words text-xl font-black text-slate-950">
            {approval.project_code} | {approval.project_name}
          </h4>
          <p className="mt-1 break-words text-sm font-semibold text-slate-600">{approval.trainer_item_name}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-right">
          <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">Deadline Proposal</div>
          <div className="mt-1 text-lg font-black text-slate-950">{formatDeadlineAmount(approval)}</div>
        </div>
      </div>

      <div className="grid gap-4 px-5 py-5 md:grid-cols-2 xl:grid-cols-3">
        <DetailBlock label="End User" value={approval.end_user} />
        <DetailBlock label="PO Deadline" value={approval.po_deadline_date} />
        {globalExtension && <DetailBlock label="Overdue Node" value={approval.target_node_label || approval.target_node || "-"} />}
        {globalExtension && <DetailBlock label="Responsible" value={approval.responsible_user_name || approval.responsible_user || "-"} />}
        {globalExtension && <DetailBlock label="Current Due" value={formatApprovalDateTime(approval.deadline_due_at)} />}
        <DetailBlock label="Submitted By" value={approval.submitted_by_name || approval.submitted_by || "-"} />
        <DetailBlock label="Submitted At" value={formatApprovalDateTime(approval.submitted_at || approval.created_at)} />
        <DetailBlock label="Project Owner" value={approval.project_owner_name || approval.project_owner || "-"} />
        {approval.comments && <DetailBlock className="md:col-span-2 xl:col-span-3" label={globalExtension ? "Overdue Details" : "Comment"} value={approval.comments} />}
        {!globalExtension && <DetailBlock className="md:col-span-2 xl:col-span-3" label="Case" value={approval.case_classification || "-"} />}
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-4">
        {handoverFailure ? (
          <>
            <Button className="min-h-9 px-3" type="button" onClick={() => onApprove({ action: "continue_anyway" })}>
              <CheckCircle2 className="h-4 w-4" />
              Continue Anyway
            </Button>
            <Button className="min-h-9 px-3" variant="danger" type="button" onClick={() => onApprove({ action: "reset_command_center" })}>
              <X className="h-4 w-4" />
              Reset Command Center
            </Button>
          </>
        ) : (
          <Button className="min-h-9 px-3" type="button" onClick={() => onApprove()}>
            <CheckCircle2 className="h-4 w-4" />
            {globalExtension ? "Approve Extension" : "Approve"}
          </Button>
        )}
        {globalExtension && (
          <Button className="min-h-9 px-3" variant="secondary" type="button" disabled>
            <X className="h-4 w-4" />
            Deny
          </Button>
        )}
        {canDeny && (
          <Button className="min-h-9 px-3" variant="danger" type="button" onClick={onDeny}>
            <X className="h-4 w-4" />
            Deny
          </Button>
        )}
        {canEdit && (
          <Button className="min-h-9 px-3" variant="secondary" type="button" onClick={onEdit}>
            <PencilLine className="h-4 w-4" />
            Edit
          </Button>
        )}
      </div>
    </article>
  );
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <label className="flex h-full flex-col justify-end">
      <span className="min-h-5 text-xs font-black uppercase tracking-wide text-slate-500">{label}</span>
      <select className="focus-ring mt-2 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="all">All</option>
        {options.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}

function DetailBlock({ label, value, className = "" }: { label: string; value: string | number; className?: string }) {
  return (
    <div className={`rounded-md border border-slate-200 bg-slate-50 p-3 ${className}`}>
      <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 whitespace-pre-wrap break-words text-sm font-semibold leading-6 text-slate-800">{String(value || "-")}</div>
    </div>
  );
}

function EmptyApprovals({ message }: { message: string }) {
  return <div className="rounded-md border border-dashed border-slate-300 p-8 text-center text-sm font-bold text-slate-500">{message}</div>;
}

function uniqueSorted(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

function approvalDepartment(approval: ApprovalRow) {
  return approval.approval_department || "SRS";
}

function approvalDepartmentTabs(approvals: ApprovalRow[]) {
  const counts = new Map<string, number>();
  approvals.forEach((approval) => {
    const department = approvalDepartment(approval);
    counts.set(department, (counts.get(department) || 0) + 1);
  });
  const knownTabs = approvalDepartmentOrder.map((department) => ({
    value: department,
    label: department,
    count: counts.get(department) || 0,
  }));
  const extraTabs = Array.from(counts)
    .filter(([department]) => !approvalDepartmentOrder.includes(department))
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([department, count]) => ({ value: department, label: department, count }));
  return [{ value: "all", label: "All", count: approvals.length }, ...knownTabs, ...extraTabs];
}

function filterAndSortApprovals(
  approvals: ApprovalRow[],
  filters: { search: string; departmentFilter: string; typeFilter: string; priorityFilter: string; sortBy: string }
) {
  const needle = filters.search.trim().toLowerCase();
  const priorityRank = (priority: string) => (priority.toLowerCase() === "high" ? 0 : 1);

  return approvals
    .filter((approval) => {
      if (filters.departmentFilter !== "all" && approvalDepartment(approval) !== filters.departmentFilter) return false;
      if (filters.typeFilter !== "all" && approval.approval_label !== filters.typeFilter) return false;
      if (filters.priorityFilter !== "all" && approval.priority !== filters.priorityFilter) return false;
      if (!needle) return true;

      return [
        approvalDepartment(approval),
        approval.approval_label,
        approval.project_code,
        approval.project_name,
        approval.end_user,
        approval.trainer_item_name,
        approval.submitted_by_name,
        approval.submitted_by,
        approval.project_owner_name,
        approval.project_owner,
        approval.target_node_label,
        approval.responsible_user_name,
        approval.responsible_user,
        approval.case_classification,
        approval.priority,
        approval.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle);
    })
    .sort((left, right) => {
      if (filters.sortBy === "oldest") return dateValue(left.created_at || left.submitted_at) - dateValue(right.created_at || right.submitted_at);
      if (filters.sortBy === "priority") return priorityRank(left.priority) - priorityRank(right.priority) || dateValue(right.created_at || right.submitted_at) - dateValue(left.created_at || left.submitted_at);
      if (filters.sortBy === "deadline_desc") return Number(right.deadline_proposal_days || 0) - Number(left.deadline_proposal_days || 0);
      if (filters.sortBy === "deadline_asc") return Number(left.deadline_proposal_days || 0) - Number(right.deadline_proposal_days || 0);
      if (filters.sortBy === "project") return `${left.project_code} ${left.project_name}`.localeCompare(`${right.project_code} ${right.project_name}`);
      return dateValue(right.created_at || right.submitted_at) - dateValue(left.created_at || left.submitted_at);
    });
}

function dateValue(value?: string) {
  const parsed = Date.parse(value || "");
  return Number.isNaN(parsed) ? 0 : parsed;
}

function priorityClass(priority: string) {
  return priority.toLowerCase() === "high"
    ? "rounded bg-amber-50 px-2.5 py-1 text-xs font-black text-amber-800"
    : "rounded bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-700";
}

function formatApprovalDateTime(value?: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short", timeZone: "Africa/Cairo" });
}

function formatDeadlineAmount(approval: ApprovalRow) {
  if (isGlobalDeadlineExtensionApproval(approval)) return "Set by GM";
  if (isCommandCenterApproval(approval) && approval.case_classification === COMMAND_CENTER_CASE_3) return "No deadline";
  const amount = Number(approval.deadline_proposal_days || 0);
  const unit = approval.deadline_unit_label || "day(s)";
  return `${amount} ${unit}`;
}

function isPmdpDualGateApproval(approval: ApprovalRow) {
  return approval.approval_type === "PMDP_DUAL_GATE_SRS_APPROVAL" || approval.approval_type === "PMDP_DUAL_GATE_GM_APPROVAL";
}

function isExtensionApproval(approval: ApprovalRow) {
  return approval.approval_type === "PMDP_EXTENSION_APPROVAL" || isGlobalDeadlineExtensionApproval(approval) || isSupplierExtensionApproval(approval);
}

function isGlobalDeadlineExtensionApproval(approval: ApprovalRow) {
  return approval.approval_type === "GLOBAL_DEADLINE_EXTENSION_APPROVAL";
}

function isSupplierExtensionApproval(approval: ApprovalRow) {
  return approval.approval_type === "SUPPLIER_DEADLINE_EXTENSION_APPROVAL";
}

function isHandoverFailureApproval(approval: ApprovalRow) {
  return approval.approval_type === "HANDOVER_FAILURE_GM_APPROVAL";
}

function isCommandCenterApproval(approval: ApprovalRow) {
  return approval.approval_type === "COMMAND_CENTER_GM_APPROVAL" || approval.approval_type === "COMMAND_CENTER_SRS_ARD_GM_APPROVAL" || isHandoverFailureApproval(approval);
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
  const extensionApproval = isExtensionApproval(approval);
  const globalExtension = isGlobalDeadlineExtensionApproval(approval);
  const commandCenterApproval = isCommandCenterApproval(approval);
  const [selectedCase, setSelectedCase] = useState(approval.case_classification || "");
  const requiresDeadline = extensionApproval || !commandCenterApproval || commandCenterDecisionRequiresDeadline(selectedCase);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <form
        className="w-full max-w-xl rounded-lg bg-white shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          const payload: Record<string, unknown> = {
            with_edits: true,
            deadline_proposal_days: requiresDeadline ? String(form.get("deadline_proposal_days") || "") : "",
          };
          if (!extensionApproval) {
            payload.case_classification = form.get("case_classification");
            payload.comments = form.get("comments");
          }
          onSubmit(payload);
        }}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">{globalExtension ? "Approve Extension" : "Approve With Edits"}</div>
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
          {!extensionApproval && (
            <label className="block">
              <span className="text-sm font-black text-slate-800">Case Classification</span>
              <select className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="case_classification" value={selectedCase} onChange={(event) => setSelectedCase(event.target.value)} required>
                {(commandCenterApproval ? commandCenterCaseOptions : srsCaseOptions).map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
          )}
          {requiresDeadline ? (
            <label className="block">
              <span className="text-sm font-black text-slate-800">{extensionApproval ? "Extension Duration" : "Deadline Proposal"}</span>
              <input className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="deadline_proposal_days" type="number" min={1} step={1} defaultValue={approval.deadline_proposal_days || ""} required />
            </label>
          ) : (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm font-semibold text-slate-700">Case 3 routes directly to ARD and does not require a deadline.</div>
          )}
          {extensionApproval && approval.comments && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">{globalExtension ? "Overdue Details" : "Requester Comment"}</div>
              <div className="mt-1 whitespace-pre-wrap text-slate-800">{approval.comments}</div>
            </div>
          )}
          {!extensionApproval && (
            <label className="block">
              <span className="text-sm font-black text-slate-800">Comment</span>
              <textarea className="focus-ring mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm" name="comments" rows={3} />
            </label>
          )}
        </div>
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button type="submit">{globalExtension ? "Approve Extension" : "Approve With Edits"}</Button>
        </div>
      </form>
    </div>
  );
}
