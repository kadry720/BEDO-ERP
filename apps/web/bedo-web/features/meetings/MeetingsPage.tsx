"use client";

import type { ReactNode } from "react";
import { CalendarClock, CheckCircle2, Clock, UsersRound } from "lucide-react";
import type { MeetingRow } from "./types";

export function MeetingsPage({ initialMeetings }: { initialMeetings: MeetingRow[] }) {
  const grouped = groupMeetings(initialMeetings);
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

      <MeetingSection title="Awaiting Confirmation" meetings={grouped.awaiting} tone="amber" />
      <MeetingSection title="Upcoming" meetings={grouped.upcoming} tone="blue" />
      <MeetingSection title="Overdue" meetings={grouped.overdue} tone="red" />
      <MeetingSection title="Completed" meetings={grouped.completed} tone="green" />
      {!initialMeetings.length && (
        <div className="rounded-md border border-dashed border-slate-300 bg-white p-10 text-center text-sm font-bold text-slate-500">
          No meetings to show.
        </div>
      )}
    </section>
  );
}

function MeetingSection({ title, meetings, tone }: { title: string; meetings: MeetingRow[]; tone: "amber" | "blue" | "red" | "green" }) {
  if (!meetings.length) return null;
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h3 className="text-lg font-black text-slate-950">{title}</h3>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-600">{meetings.length}</span>
      </div>
      <div className="grid gap-4 p-5 lg:grid-cols-2">
        {meetings.map((meeting) => (
          <MeetingCard key={meeting.name} meeting={meeting} tone={tone} />
        ))}
      </div>
    </section>
  );
}

function MeetingCard({ meeting, tone }: { meeting: MeetingRow; tone: "amber" | "blue" | "red" | "green" }) {
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
    </article>
  );
}

function StatusPill({ status }: { status: string }) {
  return <span className="shrink-0 rounded-full border border-current px-2 py-1 text-[11px] font-black">{status.replaceAll("_", " ")}</span>;
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
