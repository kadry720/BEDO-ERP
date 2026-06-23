"use client";

import { useMemo, useState, type ReactNode } from "react";
import { CalendarClock, CheckCircle2, ChevronDown, Clock, Loader2, UsersRound } from "lucide-react";
import { routeSegment } from "@/lib/route-ids";
import type { MeetingParticipant, MeetingRow } from "./types";

type MeetingTone = "amber" | "blue" | "red" | "green";

export function MeetingsPage({ initialMeetings, currentUser }: { initialMeetings: MeetingRow[]; currentUser: string }) {
  const [meetings, setMeetings] = useState(initialMeetings);
  const [openMeeting, setOpenMeeting] = useState("");
  const [confirmingMeeting, setConfirmingMeeting] = useState("");
  const [error, setError] = useState("");
  const grouped = useMemo(() => groupMeetings(meetings), [meetings]);

  async function refreshMeetings() {
    const response = await fetch("/api/meetings");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.error || "Meetings could not be refreshed.");
    setMeetings(data.meetings || []);
  }

  async function confirmAttendance(meeting: MeetingRow, selectedUsers: string[]) {
    setConfirmingMeeting(meeting.name);
    setError("");
    const response = await fetch(`/api/meetings/${routeSegment(meeting.name)}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_users: selectedUsers }),
    });
    const data = await response.json().catch(() => ({}));
    setConfirmingMeeting("");
    if (!response.ok) {
      setError(data?.error || "Meeting attendance could not be confirmed.");
      return;
    }
    await refreshMeetings();
    setOpenMeeting(meeting.name);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-slate-950 p-2 text-white">
            <CalendarClock className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">Meetings</div>
            <h2 className="mt-2 text-3xl font-black text-slate-950">Meeting Center</h2>
            <p className="mt-2 text-sm font-medium text-slate-600">Handover, ARD sync, and progress review meetings that need your attention.</p>
          </div>
        </div>
      </header>

      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <MeetingSection title="Awaiting Confirmation" meetings={grouped.awaiting} tone="amber" currentUser={currentUser} openMeeting={openMeeting} confirmingMeeting={confirmingMeeting} onToggle={setOpenMeeting} onConfirm={confirmAttendance} />
      <MeetingSection title="Upcoming" meetings={grouped.upcoming} tone="blue" currentUser={currentUser} openMeeting={openMeeting} confirmingMeeting={confirmingMeeting} onToggle={setOpenMeeting} onConfirm={confirmAttendance} />
      <MeetingSection title="Overdue" meetings={grouped.overdue} tone="red" currentUser={currentUser} openMeeting={openMeeting} confirmingMeeting={confirmingMeeting} onToggle={setOpenMeeting} onConfirm={confirmAttendance} />
      <MeetingSection title="Completed" meetings={grouped.completed} tone="green" currentUser={currentUser} openMeeting={openMeeting} confirmingMeeting={confirmingMeeting} onToggle={setOpenMeeting} onConfirm={confirmAttendance} />
      {!meetings.length && (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-10 text-center text-sm font-bold text-slate-500">
          No meetings to show.
        </div>
      )}
    </section>
  );
}

function MeetingSection({
  title,
  meetings,
  tone,
  currentUser,
  openMeeting,
  confirmingMeeting,
  onToggle,
  onConfirm,
}: {
  title: string;
  meetings: MeetingRow[];
  tone: MeetingTone;
  currentUser: string;
  openMeeting: string;
  confirmingMeeting: string;
  onToggle: (meeting: string) => void;
  onConfirm: (meeting: MeetingRow, selectedUsers: string[]) => Promise<void>;
}) {
  if (!meetings.length) return null;
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h3 className="text-lg font-black text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-600">{meetings.length}</span>
      </div>
      <div className="grid gap-4 p-5 lg:grid-cols-2">
        {meetings.map((meeting) => (
          <MeetingCard
            key={meeting.name}
            meeting={meeting}
            tone={tone}
            currentUser={currentUser}
            isOpen={openMeeting === meeting.name}
            isConfirming={confirmingMeeting === meeting.name}
            onToggle={() => onToggle(openMeeting === meeting.name ? "" : meeting.name)}
            onConfirm={onConfirm}
          />
        ))}
      </div>
    </section>
  );
}

function MeetingCard({
  meeting,
  tone,
  currentUser,
  isOpen,
  isConfirming,
  onToggle,
  onConfirm,
}: {
  meeting: MeetingRow;
  tone: MeetingTone;
  currentUser: string;
  isOpen: boolean;
  isConfirming: boolean;
  onToggle: () => void;
  onConfirm: (meeting: MeetingRow, selectedUsers: string[]) => Promise<void>;
}) {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const currentParticipant = meeting.participants.find((participant) => participant.user === currentUser);
  const canConfirm = Boolean(currentParticipant) && currentParticipant?.confirmation_status !== "CONFIRMED" && !["COMPLETED", "CANCELLED", "SUPERSEDED_BY_RESET"].includes(meeting.status);
  const pendingRequired = meeting.participants.filter((participant) => Number(participant.is_required || 0) && participant.confirmation_status !== "CONFIRMED");
  const candidates = meeting.confirmation_candidates || [];

  function toggleSelected(user: string) {
    setSelectedUsers((previous) => (previous.includes(user) ? previous.filter((candidate) => candidate !== user) : [...previous, user]));
  }

  return (
    <article className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase tracking-wide opacity-75">{formatMeetingType(meeting.meeting_type)}</div>
          <h4 className="mt-1 break-words text-lg font-black">{meeting.title}</h4>
        </div>
        <StatusPill status={meeting.status} />
      </div>
      {meeting.description && <p className="mt-3 line-clamp-3 text-sm font-medium opacity-80">{meeting.description}</p>}
      <div className="mt-4 grid gap-3 text-sm">
        <InfoRow icon={<Clock className="h-4 w-4" />} label="Scheduled" value={formatDateTime(meeting.scheduled_at, meeting.time_zone)} />
        <InfoRow icon={<UsersRound className="h-4 w-4" />} label="Organizer" value={meeting.organizer} />
        <InfoRow icon={<CheckCircle2 className="h-4 w-4" />} label="Participants" value={participantSummary(meeting)} />
      </div>

      <button
        type="button"
        className="mt-4 flex w-full items-center justify-between rounded-md border border-current px-3 py-2 text-sm font-black"
        aria-expanded={isOpen}
        onClick={onToggle}
      >
        <span>{isOpen ? "Hide meeting details" : "Open meeting details"}</span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="mt-4 space-y-4 rounded-md border border-current/20 bg-white/70 p-4 text-sm">
          <div className="grid gap-3 md:grid-cols-2">
            <MiniInfo label="Project" value={meeting.project || "-"} />
            <MiniInfo label="Trainer item" value={meeting.trainer_item || "-"} />
            <MiniInfo label="Workflow node" value={formatStatus(meeting.source_node || "-")} />
            <MiniInfo label="Expected end" value={formatDateTime(meeting.expected_end_at || "", meeting.time_zone)} />
          </div>

          <div>
            <div className="text-xs font-black uppercase tracking-wide opacity-60">Pending required confirmation</div>
            <div className="mt-1 font-bold">{pendingRequired.length ? pendingRequired.map(participantLabel).join(", ") : "All required leads confirmed"}</div>
          </div>

          <div>
            <div className="text-xs font-black uppercase tracking-wide opacity-60">Participants</div>
            <div className="mt-2 grid gap-2">
              {meeting.participants.map((participant) => (
                <ParticipantRow key={`${participant.user}-${participant.department}`} participant={participant} />
              ))}
            </div>
          </div>

          {canConfirm ? (
            <div className="space-y-3 rounded-md border border-slate-200 bg-white p-3 text-slate-900">
              <div>
                <div className="text-xs font-black uppercase tracking-wide text-slate-500">Optional attendees from your department</div>
                {candidates.length ? (
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    {candidates.map((candidate) => (
                      <label key={candidate} className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm font-bold">
                        <input type="checkbox" checked={selectedUsers.includes(candidate)} onChange={() => toggleSelected(candidate)} />
                        <span className="break-all">{candidate}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="mt-1 text-sm font-semibold text-slate-600">No additional active users are available for your department.</p>
                )}
              </div>
              <button
                type="button"
                className="flex w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 py-2 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isConfirming}
                onClick={() => onConfirm(meeting, selectedUsers)}
              >
                {isConfirming ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                Confirm attendance
              </button>
            </div>
          ) : (
            <div className="rounded-md border border-current/20 px-3 py-2 text-sm font-bold">
              {currentParticipant?.confirmation_status === "CONFIRMED" ? "You already confirmed attendance." : "Attendance confirmation is only available to active meeting participants."}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

function ParticipantRow({ participant }: { participant: MeetingParticipant }) {
  return (
    <div className="grid gap-1 rounded-md border border-current/20 px-3 py-2 sm:grid-cols-[1fr_auto] sm:items-center">
      <div className="min-w-0">
        <div className="break-all font-black">{participant.user}</div>
        <div className="text-xs font-bold opacity-70">{participant.department} - {formatMeetingType(participant.participation_source)}</div>
      </div>
      <span className="w-fit rounded-full border border-current px-2 py-1 text-[11px] font-black">{formatStatus(participant.confirmation_status)}</span>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  return <span className="shrink-0 rounded-full border border-current px-2 py-1 text-[11px] font-black">{formatStatus(status)}</span>;
}

function InfoRow({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <div className="text-[11px] font-black uppercase tracking-wide opacity-60">{label}</div>
        <div className="break-words font-semibold">{value || "-"}</div>
      </div>
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[11px] font-black uppercase tracking-wide opacity-60">{label}</div>
      <div className="break-words font-bold">{value || "-"}</div>
    </div>
  );
}

function groupMeetings(meetings: MeetingRow[]) {
  return {
    awaiting: meetings.filter((meeting) => meeting.status === "PENDING_CONFIRMATION"),
    overdue: meetings.filter((meeting) => meeting.status === "OVERDUE"),
    completed: meetings.filter((meeting) => meeting.status === "COMPLETED"),
    upcoming: meetings.filter((meeting) => !["PENDING_CONFIRMATION", "OVERDUE", "COMPLETED"].includes(meeting.status)),
  };
}

const toneClasses = {
  amber: "border-amber-200 bg-amber-50 text-amber-950",
  blue: "border-blue-200 bg-blue-50 text-blue-950",
  red: "border-red-200 bg-red-50 text-red-950",
  green: "border-emerald-200 bg-emerald-50 text-emerald-950",
};

function formatMeetingType(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatStatus(value: string) {
  return value.replaceAll("_", " ");
}

function participantLabel(participant: MeetingParticipant) {
  return `${participant.user} (${participant.department})`;
}

function participantSummary(meeting: MeetingRow) {
  if (!meeting.participants.length) return "No participants";
  const confirmed = meeting.participants.filter((participant) => participant.confirmation_status === "CONFIRMED").length;
  return `${meeting.participants.length} participant(s), ${confirmed} confirmed`;
}

function formatDateTime(value: string, timeZone: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short", timeZone: timeZone || "Africa/Cairo" });
}
