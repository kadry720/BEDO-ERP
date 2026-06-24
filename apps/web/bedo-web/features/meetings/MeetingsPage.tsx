"use client";

import { useMemo, useState, type ReactNode } from "react";
import { CalendarClock, CheckCircle2, Clock, Loader2, Search, UsersRound } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, Panel, PanelBody, PanelHeader } from "@/components/ui/Panel";
import { FieldLabel, FieldText, SelectInput, TextInput } from "@/components/ui/Field";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { routeSegment } from "@/lib/route-ids";
import type { MeetingParticipant, MeetingRow } from "./types";

type MeetingBucket = "all" | "awaiting" | "upcoming" | "overdue" | "completed";

export function MeetingsPage({ initialMeetings, currentUser }: { initialMeetings: MeetingRow[]; currentUser: string }) {
  const [meetings, setMeetings] = useState(initialMeetings);
  const [selectedMeetingName, setSelectedMeetingName] = useState(() => preferredMeeting(initialMeetings)?.name || "");
  const [confirmingMeeting, setConfirmingMeeting] = useState("");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [bucket, setBucket] = useState<MeetingBucket>("all");
  const [sortBy, setSortBy] = useState("scheduled");

  const visibleMeetings = useMemo(() => filterMeetings(meetings, { search, bucket, sortBy }), [meetings, search, bucket, sortBy]);
  const selectedMeeting = visibleMeetings.find((meeting) => meeting.name === selectedMeetingName) || visibleMeetings[0] || null;
  const bucketOptions = useMemo(() => meetingBucketOptions(meetings), [meetings]);

  async function refreshMeetings(nextSelectedName?: string) {
    const response = await fetch("/api/meetings");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.error || "Meetings could not be refreshed.");
    const nextMeetings = data.meetings || [];
    setMeetings(nextMeetings);
    setSelectedMeetingName(nextSelectedName || preferredMeeting(nextMeetings)?.name || "");
    window.dispatchEvent(new Event("bedo:meetings-changed"));
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
    await refreshMeetings(meeting.name);
  }

  return (
    <section className="space-y-4">
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div>}

      <Panel>
        <PanelHeader className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">Agenda</div>
              <div className="mt-1 text-sm font-semibold text-slate-600">{visibleMeetings.length} of {meetings.length} meeting(s)</div>
            </div>
            <SegmentedControl label="Meeting status" options={bucketOptions} value={bucket} onChange={(value) => setBucket(value as MeetingBucket)} />
          </div>
          <div className="grid gap-3 lg:grid-cols-[minmax(260px,1fr)_220px]">
            <FieldLabel>
              <FieldText>Search</FieldText>
              <span className="focus-within:focus-ring mt-2 flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3">
                <Search className="h-4 w-4 text-slate-400" />
                <TextInput className="mt-0 border-0 px-0 outline-none focus-visible:outline-transparent" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Project, trainer, organizer..." />
              </span>
            </FieldLabel>
            <FieldLabel>
              <FieldText>Sort</FieldText>
              <SelectInput value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                <option value="scheduled">Scheduled first</option>
                <option value="newest">Newest created</option>
                <option value="status">Status</option>
              </SelectInput>
            </FieldLabel>
          </div>
        </PanelHeader>
        <PanelBody>
          {visibleMeetings.length ? (
            <div className="grid gap-4 xl:grid-cols-[minmax(320px,430px)_1fr]">
              <MeetingAgendaList meetings={visibleMeetings} selectedMeeting={selectedMeeting} onSelect={setSelectedMeetingName} />
              {selectedMeeting && (
                <MeetingDetail
                  key={selectedMeeting.name}
                  meeting={selectedMeeting}
                  currentUser={currentUser}
                  isConfirming={confirmingMeeting === selectedMeeting.name}
                  onConfirm={confirmAttendance}
                />
              )}
            </div>
          ) : (
            <EmptyState title="No meetings match the current filters." description="Change the search or status filter to see more agenda items." />
          )}
        </PanelBody>
      </Panel>
    </section>
  );
}

function MeetingAgendaList({ meetings, selectedMeeting, onSelect }: { meetings: MeetingRow[]; selectedMeeting: MeetingRow | null; onSelect: (meeting: string) => void }) {
  const groups = groupMeetingsByDate(meetings);
  return (
    <div className="min-w-0 rounded-md border border-slate-200">
      {groups.map((group) => (
        <section key={group.label} className="border-b border-slate-200 last:border-b-0">
          <div className="bg-slate-50 px-4 py-2 text-xs font-black uppercase tracking-wide text-slate-500">{group.label}</div>
          <div className="divide-y divide-slate-100">
            {group.rows.map((meeting) => {
              const active = selectedMeeting?.name === meeting.name;
              return (
                <button
                  key={meeting.name}
                  type="button"
                  className={`focus-ring block w-full px-4 py-3 text-left transition ${active ? "bg-slate-950 text-white" : "bg-white hover:bg-slate-50"}`}
                  onClick={() => onSelect(meeting.name)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className={`text-[11px] font-black uppercase tracking-wide ${active ? "text-slate-300" : "text-slate-500"}`}>{formatMeetingType(meeting.meeting_type)}</div>
                      <div className="mt-1 truncate text-sm font-black">{meeting.title}</div>
                      <div className={`mt-1 truncate text-xs font-semibold ${active ? "text-slate-300" : "text-slate-500"}`}>{meetingProjectLabel(meeting)}</div>
                    </div>
                    <MeetingStatusBadge status={meeting.status} />
                  </div>
                  <div className={`mt-2 flex items-center gap-2 text-xs font-semibold ${active ? "text-slate-300" : "text-slate-600"}`}>
                    <Clock className="h-3.5 w-3.5" />
                    {formatDateTime(meeting.scheduled_at, meeting.time_zone)}
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

function MeetingDetail({ meeting, currentUser, isConfirming, onConfirm }: { meeting: MeetingRow; currentUser: string; isConfirming: boolean; onConfirm: (meeting: MeetingRow, selectedUsers: string[]) => Promise<void> }) {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const currentParticipant = meeting.participants.find((participant) => participant.user === currentUser);
  const canConfirm = Boolean(currentParticipant) && currentParticipant?.confirmation_status !== "CONFIRMED" && !["COMPLETED", "CANCELLED", "SUPERSEDED_BY_RESET"].includes(meeting.status);
  const pendingRequired = meeting.participants.filter((participant) => Number(participant.is_required || 0) && participant.confirmation_status !== "CONFIRMED");
  const candidates = meeting.confirmation_candidates || [];
  const handoverPaths = meeting.handover_paths || [];

  function toggleSelected(user: string) {
    setSelectedUsers((previous) => (previous.includes(user) ? previous.filter((candidate) => candidate !== user) : [...previous, user]));
  }

  return (
    <article className="min-w-0 rounded-md border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="slate">{formatMeetingType(meeting.meeting_type)}</Badge>
              <MeetingStatusBadge status={meeting.status} />
            </div>
            <h3 className="mt-3 break-words text-2xl font-black text-slate-950">{meeting.title}</h3>
            {meeting.description && <p className="mt-2 max-w-3xl text-sm font-semibold leading-6 text-slate-600">{meeting.description}</p>}
          </div>
        </div>
      </div>

      <div className="grid gap-5 px-5 py-5">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <InfoBlock icon={<CalendarClock className="h-4 w-4" />} label="Scheduled" value={formatDateTime(meeting.scheduled_at, meeting.time_zone)} />
          <InfoBlock icon={<Clock className="h-4 w-4" />} label="Expected End" value={formatDateTime(meeting.expected_end_at || "", meeting.time_zone)} />
          <InfoBlock icon={<UsersRound className="h-4 w-4" />} label="Organizer" value={meeting.organizer} />
          <InfoBlock icon={<CheckCircle2 className="h-4 w-4" />} label="Project" value={meetingProjectLabel(meeting)} />
          <InfoBlock icon={<CheckCircle2 className="h-4 w-4" />} label="Trainer Item" value={meeting.trainer_item || "-"} />
          <InfoBlock icon={<CheckCircle2 className="h-4 w-4" />} label="Workflow Node" value={formatStatus(meeting.source_node || "-")} />
        </div>

        {handoverPaths.length > 0 && (
          <section>
            <div className="text-xs font-black uppercase tracking-wide text-slate-500">Handover Paths</div>
            <div className="mt-2 grid gap-2">
              {handoverPaths.map((item) => (
                <div key={`${item.label}-${item.path}`} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
                  <div className="text-[11px] font-black uppercase tracking-wide text-slate-500">{item.label}</div>
                  <div className="break-words text-sm font-bold text-slate-950">{item.path}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section>
          <div className="text-xs font-black uppercase tracking-wide text-slate-500">Pending Required Confirmation</div>
          <div className="mt-1 text-sm font-bold text-slate-800">{pendingRequired.length ? pendingRequired.map(participantLabel).join(", ") : "All required leads confirmed"}</div>
        </section>

        <section>
          <div className="text-xs font-black uppercase tracking-wide text-slate-500">Participants</div>
          <div className="mt-2 grid gap-2">
            {meeting.participants.map((participant) => <ParticipantRow key={`${participant.user}-${participant.department}`} participant={participant} />)}
          </div>
        </section>

        {canConfirm ? (
          <section className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-4">
            <div>
              <div className="text-xs font-black uppercase tracking-wide text-slate-500">Optional Attendees From Your Department</div>
              {candidates.length ? (
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {candidates.map((candidate) => (
                    <label key={candidate} className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-bold">
                      <input type="checkbox" checked={selectedUsers.includes(candidate)} onChange={() => toggleSelected(candidate)} />
                      <span className="break-all">{candidate}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-sm font-semibold text-slate-600">No additional active users are available for your department.</p>
              )}
            </div>
            <Button type="button" disabled={isConfirming} onClick={() => onConfirm(meeting, selectedUsers)}>
              {isConfirming ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              Confirm attendance
            </Button>
          </section>
        ) : (
          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-bold text-slate-700">
            {currentParticipant?.confirmation_status === "CONFIRMED" ? "You already confirmed attendance." : "Attendance confirmation is only available to active meeting participants."}
          </div>
        )}
      </div>
    </article>
  );
}

function ParticipantRow({ participant }: { participant: MeetingParticipant }) {
  return (
    <div className="grid gap-1 rounded-md border border-slate-200 bg-white px-3 py-2 sm:grid-cols-[1fr_auto] sm:items-center">
      <div className="min-w-0">
        <div className="break-all font-black text-slate-950">{participant.user}</div>
        <div className="text-xs font-bold text-slate-500">{participant.department} - {formatMeetingType(participant.participation_source)}</div>
      </div>
      <Badge tone={participant.confirmation_status === "CONFIRMED" ? "green" : "amber"}>{formatStatus(participant.confirmation_status)}</Badge>
    </div>
  );
}

function MeetingStatusBadge({ status }: { status: string }) {
  const tone = status === "COMPLETED" ? "green" : status === "OVERDUE" ? "red" : status === "PENDING_CONFIRMATION" ? "amber" : "blue";
  return <Badge tone={tone}>{formatStatus(status)}</Badge>;
}

function InfoBlock({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-wide text-slate-500">
        {icon}
        {label}
      </div>
      <div className="mt-1 break-words text-sm font-semibold text-slate-950">{value || "-"}</div>
    </div>
  );
}

function preferredMeeting(meetings: MeetingRow[]) {
  return meetings.find((meeting) => meeting.status === "PENDING_CONFIRMATION") || meetings.find((meeting) => meeting.status === "OVERDUE") || meetings[0];
}

function filterMeetings(meetings: MeetingRow[], filters: { search: string; bucket: MeetingBucket; sortBy: string }) {
  const needle = filters.search.trim().toLowerCase();
  return meetings
    .filter((meeting) => {
      if (filters.bucket !== "all" && bucketForMeeting(meeting) !== filters.bucket) return false;
      if (!needle) return true;
      return [meeting.title, meeting.meeting_type, meeting.project_code, meeting.project_name, meeting.trainer_item, meeting.organizer, meeting.status]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle);
    })
    .sort((left, right) => {
      if (filters.sortBy === "newest") return dateValue(right.created_at) - dateValue(left.created_at);
      if (filters.sortBy === "status") return left.status.localeCompare(right.status) || dateValue(left.scheduled_at) - dateValue(right.scheduled_at);
      return dateValue(left.scheduled_at) - dateValue(right.scheduled_at);
    });
}

function meetingBucketOptions(meetings: MeetingRow[]) {
  const counts = meetings.reduce(
    (acc, meeting) => {
      acc.all += 1;
      acc[bucketForMeeting(meeting)] += 1;
      return acc;
    },
    { all: 0, awaiting: 0, upcoming: 0, overdue: 0, completed: 0 } as Record<MeetingBucket, number>
  );
  return [
    { value: "all", label: "All", count: counts.all },
    { value: "awaiting", label: "Awaiting", count: counts.awaiting },
    { value: "upcoming", label: "Upcoming", count: counts.upcoming },
    { value: "overdue", label: "Overdue", count: counts.overdue },
    { value: "completed", label: "Completed", count: counts.completed },
  ];
}

function bucketForMeeting(meeting: MeetingRow): MeetingBucket {
  if (meeting.status === "PENDING_CONFIRMATION") return "awaiting";
  if (meeting.status === "OVERDUE") return "overdue";
  if (meeting.status === "COMPLETED") return "completed";
  return "upcoming";
}

function groupMeetingsByDate(meetings: MeetingRow[]) {
  const groups = new Map<string, MeetingRow[]>();
  for (const meeting of meetings) {
    const label = dateGroupLabel(meeting.scheduled_at, meeting.time_zone);
    groups.set(label, [...(groups.get(label) || []), meeting]);
  }
  return Array.from(groups, ([label, rows]) => ({ label, rows }));
}

function dateGroupLabel(value: string, timeZone: string) {
  if (!value) return "Unscheduled";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unscheduled";
  return date.toLocaleDateString("en-US", { dateStyle: "medium", timeZone: timeZone || "Africa/Cairo" });
}

function dateValue(value?: string) {
  const parsed = Date.parse(value || "");
  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatMeetingType(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatStatus(value: string) {
  return value.replaceAll("_", " ");
}

function participantLabel(participant: MeetingParticipant) {
  return `${participant.user} (${participant.department})`;
}

function meetingProjectLabel(meeting: MeetingRow) {
  return [meeting.project_code || meeting.project, meeting.project_name].filter(Boolean).join(" - ") || "-";
}

function formatDateTime(value: string, timeZone: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short", timeZone: timeZone || "Africa/Cairo" });
}
