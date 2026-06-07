"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Plus, Rocket, Trash2 } from "lucide-react";
import { Button } from "@/components/Button";
import type { BedoProject, SafeUser, TrainerItem, TrainerItemList } from "@/features/srs/types";
import { formatNodeId, formatStatus, statusBadgeClass } from "@/features/srs/workflowPresentation";

type Props = {
  project: BedoProject;
  initialItems: TrainerItemList;
  mode: "gm" | "srs";
};

type PendingTrainer = {
  trainer_name: string;
  quantity: number;
  report_to_users: string[];
};

export function ProjectDetail({ project, initialItems, mode }: Props) {
  const [items, setItems] = useState(initialItems.trainer_items);
  const [projectState, setProjectState] = useState(project);
  const [reportToUsers, setReportToUsers] = useState<SafeUser[]>([]);
  const [pendingTrainer, setPendingTrainer] = useState<PendingTrainer | null>(null);
  const [editing, setEditing] = useState<TrainerItem | null>(null);
  const [error, setError] = useState("");
  const isGm = mode === "gm";
  const locked = projectState.status === "RELEASED_TO_SRS" || projectState.status === "IN_SRS";
  const canManageItems = isGm && projectState.status === "DETAILS_FINALIZED" && !locked;
  const itemRouteBase = mode === "gm" ? `/gm/projects/${project.name}/items` : `/srs/projects/${project.name}/items`;

  useEffect(() => {
    if (isGm) {
      fetch("/api/report-to-candidates")
        .then((response) => response.json())
        .then((data) => setReportToUsers(data.users || []))
        .catch(() => setReportToUsers([]));
    }
  }, [isGm]);

  const defaultReportTo = useMemo(() => {
    const gm = reportToUsers.find((user) => user.business_role === "General Manager");
    return gm ? [gm.user] : [];
  }, [reportToUsers]);

  async function refreshItems() {
    const response = await fetch(`/api/projects/${project.name}/trainer-items`);
    if (response.ok) setItems((await response.json()).trainer_items);
  }

  async function finalizeProject() {
    setError("");
    const response = await fetch(`/api/projects/${project.name}/finalize`, { method: "POST" });
    if (!response.ok) {
      setError("Project details could not be finalized.");
      return;
    }
    setProjectState((await response.json()).project);
  }

  async function releaseProject() {
    setError("");
    const response = await fetch(`/api/projects/${project.name}/release-srs`, { method: "POST" });
    if (!response.ok) {
      setError("Project could not be released. Make sure details are finalized and trainer items exist.");
      return;
    }
    const data = await response.json();
    setProjectState(data.project);
    setItems(data.trainer_items);
  }

  async function submitTrainer(payload: PendingTrainer & { separation_mode?: string }) {
    const response = await fetch(editing ? `/api/trainer-items/${editing.name}` : `/api/projects/${project.name}/trainer-items`, {
      method: editing ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      setError("Trainer item could not be saved.");
      return;
    }
    setPendingTrainer(null);
    setEditing(null);
    await refreshItems();
  }

  async function handleTrainerSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      trainer_name: String(form.get("trainer_name") || "").trim(),
      quantity: Number(form.get("quantity") || 1),
      report_to_users: form.getAll("report_to_users").map(String)
    };
    if (payload.quantity > 1 && !editing) {
      setPendingTrainer(payload);
      return;
    }
    await submitTrainer({ ...payload, separation_mode: editing?.separation_mode || "SINGLE" });
    formElement.reset();
  }

  async function deleteItem(item: TrainerItem) {
    const response = await fetch(`/api/trainer-items/${item.name}`, { method: "DELETE" });
    if (response.ok) await refreshItems();
  }

  return (
    <section className="space-y-6">
      <header className="rounded-md border border-gray-200 bg-white p-6 shadow-panel">
        <div className="text-xs font-bold uppercase text-muted">{projectState.project_code}</div>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-ink">{projectState.project_name}</h1>
            <p className="mt-2 text-sm text-muted">End user: {projectState.end_user} | PO deadline: {projectState.po_deadline_date}</p>
          </div>
          <span className={`rounded-full border px-3 py-2 text-sm font-bold ${statusBadgeClass(projectState.status)}`}>{formatStatus(projectState.status)}</span>
        </div>
      </header>

      {error && <div className="rounded-md bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">{error}</div>}

      {isGm && projectState.status === "DRAFT" && (
        <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
          <h2 className="text-lg font-bold text-ink">Step 1: Project Details</h2>
          <p className="mt-1 text-sm text-muted">Details are complete. Finalize them to unlock the trainer-items table.</p>
          <Button className="mt-4" type="button" onClick={finalizeProject}>
            <CheckCircle2 className="h-4 w-4" />
            Finalize Project Details
          </Button>
        </div>
      )}

      {isGm && canManageItems && (
        <form className="rounded-md border border-gray-200 bg-white p-5 shadow-panel" onSubmit={handleTrainerSubmit}>
          <div className="mb-4">
            <h2 className="text-lg font-bold text-ink">{editing ? "Edit Trainer Item" : "Step 2: Trainer Items"}</h2>
            <p className="text-sm text-muted">Trainer items own SRS workflow instances. Projects do not have flowcharts.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-[1fr_140px_2fr_auto]">
            <label className="block">
              <span className="text-sm font-semibold text-ink">Trainer Name</span>
              <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" name="trainer_name" defaultValue={editing?.trainer_name || ""} required />
            </label>
            <label className="block">
              <span className="text-sm font-semibold text-ink">Quantity</span>
              <input className="focus-ring mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm" min={1} name="quantity" type="number" defaultValue={editing?.quantity || 1} required />
            </label>
            <div>
              <div className="text-sm font-semibold text-ink">Report To</div>
              <div className="mt-2 flex max-h-24 flex-wrap gap-2 overflow-auto rounded-md border border-gray-200 p-2">
                {reportToUsers.map((user) => (
                  <label key={user.user} className="cursor-pointer">
                    <input className="peer sr-only" name="report_to_users" type="checkbox" value={user.user} defaultChecked={!editing && defaultReportTo.includes(user.user)} />
                    <span className="block rounded-md border border-gray-300 px-3 py-2 text-xs font-semibold peer-checked:border-ember peer-checked:bg-orange-50">
                      {user.full_name}
                    </span>
                  </label>
                ))}
                {!reportToUsers.length && <span className="text-sm text-muted">No GM Support Office users found.</span>}
              </div>
            </div>
            <div className="flex items-end gap-2">
              <Button type="submit">
                <Plus className="h-4 w-4" />
                {editing ? "Save" : "Add"}
              </Button>
              {editing && (
                <Button variant="secondary" type="button" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
        </form>
      )}

      <div className="rounded-md border border-gray-200 bg-white p-5 shadow-panel">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-ink">Trainer Items</h2>
            <p className="text-sm text-muted">{items.length} item(s)</p>
          </div>
          {isGm && projectState.status === "DETAILS_FINALIZED" && (
            <Button type="button" disabled={!items.length} onClick={releaseProject}>
              <Rocket className="h-4 w-4" />
              Release PO to SRS
            </Button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-xs uppercase text-muted">
              <tr>
                <th className="py-3 pr-4">Trainer Item</th>
                <th className="py-3 pr-4">Quantity</th>
                <th className="py-3 pr-4">Mode</th>
                <th className="py-3 pr-4">Current SRS Node</th>
                <th className="py-3 pr-4">Responsible</th>
                <th className="py-3 pr-4">Deadline Due</th>
                <th className="py-3 pr-4">Status</th>
                <th className="py-3 pr-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.name}>
                  <td className="py-3 pr-4 font-semibold text-ink">
                    <Link href={`${itemRouteBase}/${item.name}`}>{item.trainer_item_name}</Link>
                  </td>
                  <td className="py-3 pr-4">{item.quantity}</td>
                  <td className="py-3 pr-4">{formatStatus(item.separation_mode)}</td>
                  <td className="py-3 pr-4">{formatNodeId(item.workflow?.current_node || item.current_node)}</td>
                  <td className="py-3 pr-4">{item.current_responsible_user || item.workflow?.project_owner || "-"}</td>
                  <td className="py-3 pr-4">{item.deadline?.due_at || "-"}</td>
                  <td className="py-3 pr-4">
                    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-bold ${statusBadgeClass(item.status)}`}>
                      {formatStatus(item.status)}
                    </span>
                  </td>
                  <td className="py-3 pr-4">
                    {canManageItems && (
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary" type="button" onClick={() => setEditing(item)}>
                          Edit
                        </Button>
                        <Button variant="danger" type="button" onClick={() => deleteItem(item)}>
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length && <div className="rounded-md border border-dashed border-gray-300 p-6 text-sm text-muted">No trainer items yet.</div>}
        </div>
      </div>

      {pendingTrainer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-md bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold text-ink">Quantity Handling</h3>
            <p className="mt-2 text-sm text-muted">
              Quantity is {pendingTrainer.quantity}. Choose whether these units share one SRS flowchart or split into independent trainer items.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <Button type="button" onClick={() => submitTrainer({ ...pendingTrainer, separation_mode: "COMBINED" })}>
                Combined
              </Button>
              <Button variant="secondary" type="button" onClick={() => submitTrainer({ ...pendingTrainer, separation_mode: "SEPARATED" })}>
                Separated
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
