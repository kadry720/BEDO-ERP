"use client";

import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Route } from "lucide-react";
import { workflowStatusIcons, workflowToneStyles } from "./workflow-theme";
import type {
  WorkflowCanvasHeaderStat,
  WorkflowConnectorRoute,
  WorkflowDeadlineBand,
  WorkflowDeadlineColumn,
  WorkflowDimensions,
  WorkflowIcon,
  WorkflowLaneBand,
  WorkflowNode,
  WorkflowNodeAvailability,
  WorkflowNodeState,
  WorkflowTone,
} from "./workflow-types";

type WorkflowCanvasProps<TNode extends WorkflowNode, TState extends WorkflowNodeState, TAvailability extends WorkflowNodeAvailability> = {
  eyebrow: string;
  title: string;
  subtitle: string;
  dimensions: WorkflowDimensions;
  laneBands: WorkflowLaneBand[];
  deadlineBands: WorkflowDeadlineBand[];
  deadlineColumns: WorkflowDeadlineColumn[];
  nodes: TNode[];
  edges: Array<{ from: string; to: string }>;
  states: Map<string, TState>;
  availability: Map<string, TAvailability>;
  headerStats: WorkflowCanvasHeaderStat[];
  markerId: string;
  connectorRoutes: Record<string, WorkflowConnectorRoute>;
  activeDeadlineState?: TState;
  now: Date;
  status: string;
  nodeIcons?: Record<string, WorkflowIcon>;
  nodeSubtitles?: Record<string, string>;
  canOpenNode: (node: TNode, state?: TState, availability?: TAvailability) => boolean;
  isDeadlineOverdue: (state: TState | undefined, now: Date) => boolean;
  statusTone: (status?: string | null) => WorkflowTone;
  formatStatus: (status?: string | null) => string;
  nodeSummary?: (nodeId: string, state?: TState) => string;
  positionForNode: (node: Pick<TNode, "id">) => { x: number; y: number; w: number; h: number };
  anchorPoint: (nodeId: string, side: WorkflowConnectorRoute["fromSide"]) => { x: number; y: number };
  renderStatusBadge: (status?: string | null) => ReactNode;
  renderDeadlineBadge: (state: TState, compact?: boolean) => ReactNode;
  onOpenNode: (nodeId: string) => void;
  children?: ReactNode;
};

export function WorkflowCanvas<TNode extends WorkflowNode, TState extends WorkflowNodeState, TAvailability extends WorkflowNodeAvailability>({
  eyebrow,
  title,
  subtitle,
  dimensions,
  laneBands,
  deadlineBands,
  deadlineColumns,
  nodes,
  edges,
  states,
  availability,
  headerStats,
  markerId,
  connectorRoutes,
  activeDeadlineState,
  now,
  status,
  nodeIcons,
  nodeSubtitles,
  canOpenNode,
  isDeadlineOverdue,
  statusTone,
  formatStatus,
  nodeSummary,
  positionForNode,
  anchorPoint,
  renderStatusBadge,
  renderDeadlineBadge,
  onOpenNode,
  children,
}: WorkflowCanvasProps<TNode, TState, TAvailability>) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const diagramWidth = dimensions.laneLabelWidth + dimensions.canvasWidth;
  const diagramHeight = dimensions.deadlineHeaderHeight + dimensions.canvasHeight;
  const deadlineColumnMeta = useMemo(() => new Map(deadlineColumns.map((column) => [column.id, column])), [deadlineColumns]);

  useLayoutEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    const updateScale = () => {
      const availableWidth = frame.clientWidth;
      setScale(Math.min(1, availableWidth / diagramWidth));
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(frame);
    return () => observer.disconnect();
  }, [diagramWidth]);

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4 shadow-panel md:p-5">
      <div className="mb-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-900 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">{eyebrow}</p>
            <h2 className="mt-1 text-lg font-bold text-white">{title}</h2>
            <p className="text-xs text-slate-300">{subtitle}</p>
          </div>
          {activeDeadlineState ? renderDeadlineBadge(activeDeadlineState) : renderStatusBadge(status)}
        </div>

        <div className="grid grid-cols-2 gap-px bg-slate-100 lg:grid-cols-4">
          {headerStats.map((stat) => (
            stat.label.toLowerCase().includes("progress") ? (
              <HeaderStatProgress key={stat.label} label={stat.label} value={Number.parseInt(stat.value, 10) || 0} />
            ) : (
              <HeaderStat key={stat.label} label={stat.label} value={stat.value} tone={stat.tone} />
            )
          ))}
        </div>
      </div>

      <WorkflowLegend />

      <div
        ref={frameRef}
        className="overflow-hidden rounded-md border border-slate-200 bg-white"
        style={{
          backgroundColor: "#f8fafc",
          backgroundImage:
            "linear-gradient(to right, rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.10) 1px, transparent 1px)",
          backgroundSize: `${32 * scale}px ${32 * scale}px`,
        }}
      >
        <div style={{ minWidth: diagramWidth * scale, width: "100%", height: diagramHeight * scale }}>
          <div style={{ width: diagramWidth, transform: `scale(${scale})`, transformOrigin: "top left" }}>
            {dimensions.deadlineHeaderHeight > 0 && deadlineBands.length > 0 && (
              <div className="flex border-b border-slate-200 bg-slate-100">
                <div className="shrink-0 border-r border-slate-200" style={{ width: dimensions.laneLabelWidth }} />
                <div className="relative" style={{ width: dimensions.canvasWidth, height: dimensions.deadlineHeaderHeight }}>
                  {deadlineBands.map((column, index) => (
                    <div key={column.id} className={`absolute top-0 h-full ${index > 0 ? "border-l border-slate-300" : ""}`} style={{ left: column.x, width: column.w }}>
                      <DeadlineHeader label={deadlineColumnMeta.get(column.id)?.label || column.label} detail={deadlineColumnMeta.get(column.id)?.detail || column.detail} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex">
              <div className="relative shrink-0 border-r border-slate-200" style={{ width: dimensions.laneLabelWidth, height: dimensions.canvasHeight }}>
                {laneBands.map((lane, index) => (
                  <div
                    key={lane.id}
                    className={`absolute left-0 flex w-full items-center justify-center px-4 text-center ${index > 0 ? "border-t border-slate-700/40" : ""}`}
                    style={{ top: lane.y, height: lane.h, backgroundColor: index % 2 === 0 ? "#1e293b" : "#0f172a" }}
                  >
                    <span>
                      <span className="block text-[13px] font-semibold uppercase tracking-wide text-slate-100">{deadlineColumnMeta.get(lane.id)?.label || lane.label}</span>
                      <span className="mt-1 block text-[11px] font-medium leading-snug text-slate-300">{deadlineColumnMeta.get(lane.id)?.detail || lane.detail}</span>
                    </span>
                  </div>
                ))}
              </div>

              <div
                className="relative"
                style={{
                  width: dimensions.canvasWidth,
                  height: dimensions.canvasHeight,
                  backgroundColor: "#f8fafc",
                  backgroundImage:
                    "linear-gradient(to right, rgba(148,163,184,0.10) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.10) 1px, transparent 1px)",
                  backgroundSize: "32px 32px",
                }}
              >
                {laneBands.map((lane, index) => (
                  <div
                    key={lane.id}
                    className="absolute left-0 w-full"
                    style={{
                      top: lane.y,
                      height: lane.h,
                      backgroundColor: index % 2 === 1 ? "rgba(148,163,184,0.05)" : "transparent",
                      borderTop: index > 0 ? "1px dashed rgba(148,163,184,0.45)" : "none",
                    }}
                  />
                ))}

                {deadlineBands.map((column, index) => (
                  <div
                    key={column.id}
                    className={`absolute top-0 h-full ${index > 0 ? "border-l border-dashed border-slate-300" : ""}`}
                    style={{
                      left: column.x,
                      width: column.w,
                      backgroundColor: index % 2 === 0 ? "rgba(241,245,249,0.55)" : "rgba(255,255,255,0.44)",
                    }}
                  />
                ))}

                <svg className="pointer-events-none absolute inset-0" width={dimensions.canvasWidth} height={dimensions.canvasHeight}>
                  <defs>
                    <marker id={markerId} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                    </marker>
                  </defs>
                  {edges.map((edge) => {
                    const path = edgePath(edge.from, edge.to, connectorRoutes, anchorPoint);
                    const sourceStatus = states.get(edge.from)?.status;
                    const targetStatus = states.get(edge.to)?.status;
                    const notApplicable = sourceStatus === "NOT_APPLICABLE" || targetStatus === "NOT_APPLICABLE";
                    const active = sourceStatus === "COMPLETED" && !notApplicable;
                    return (
                      <path
                        key={`${edge.from}-${edge.to}`}
                        d={path}
                        fill="none"
                        markerEnd={`url(#${markerId})`}
                        stroke={notApplicable ? "#020617" : active ? "#16a34a" : "#94a3b8"}
                        strokeDasharray={notApplicable ? "2 7" : undefined}
                        opacity={notApplicable ? 0.5 : 1}
                        strokeLinecap="round"
                        strokeWidth={active ? 2.5 : 1.75}
                      />
                    );
                  })}
                </svg>

                {activeDeadlineState && (
                  <div className="absolute" style={countdownPosition(activeDeadlineState.node_id, positionForNode)}>
                    {renderDeadlineBadge(activeDeadlineState, true)}
                  </div>
                )}

                {nodes.map((node) => {
                  const state = states.get(node.id);
                  const available = availability.get(node.id);
                  return (
                    <WorkflowNodeCard
                      key={node.id}
                      node={node}
                      state={state}
                      availability={available}
                      now={now}
                      nodeIcons={nodeIcons}
                      nodeSubtitles={nodeSubtitles}
                      canOpenNode={canOpenNode}
                      isDeadlineOverdue={isDeadlineOverdue}
                      statusTone={statusTone}
                      formatStatus={formatStatus}
                      nodeSummary={nodeSummary}
                      positionForNode={positionForNode}
                      onOpen={() => {
                        if (canOpenNode(node, state, available)) onOpenNode(node.id);
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {children}
    </div>
  );
}

function HeaderStat({ label, value, tone }: { label: string; value: string; tone?: WorkflowTone }) {
  return (
    <div className="bg-white px-5 py-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-0.5 truncate text-sm font-semibold" style={{ color: tone ? workflowToneStyles[tone].chipText : "#1e293b" }}>
        {value || "-"}
      </p>
    </div>
  );
}

function HeaderStatProgress({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white px-5 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
        <span className="text-xs font-bold text-slate-700">{value}%</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-slate-800" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

export function WorkflowLegend() {
  return (
    <div className="mb-5 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border border-slate-200 bg-white px-4 py-3">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Legend</span>
      {(["complete", "in-progress", "pending", "awaiting-approval", "locked", "not-applicable", "overdue"] as const).map((tone) => (
        <span key={tone} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: workflowToneStyles[tone].dot }} />
          <span className="text-xs font-medium text-slate-600">{workflowToneStyles[tone].label}</span>
        </span>
      ))}
    </div>
  );
}

function DeadlineHeader({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-0.5 px-3 text-center">
      <span className="text-[13px] font-bold uppercase tracking-wide text-slate-700">{label}</span>
      <span className="text-[11px] font-medium text-slate-500">{detail}</span>
    </div>
  );
}

function WorkflowNodeCard<TNode extends WorkflowNode, TState extends WorkflowNodeState, TAvailability extends WorkflowNodeAvailability>({
  node,
  state,
  availability,
  now,
  nodeIcons,
  nodeSubtitles,
  canOpenNode,
  isDeadlineOverdue,
  statusTone,
  formatStatus,
  nodeSummary,
  positionForNode,
  onOpen,
}: {
  node: TNode;
  state?: TState;
  availability?: TAvailability;
  now: Date;
  nodeIcons?: Record<string, WorkflowIcon>;
  nodeSubtitles?: Record<string, string>;
  canOpenNode: (node: TNode, state?: TState, availability?: TAvailability) => boolean;
  isDeadlineOverdue: (state: TState | undefined, now: Date) => boolean;
  statusTone: (status?: string | null) => WorkflowTone;
  formatStatus: (status?: string | null) => string;
  nodeSummary?: (nodeId: string, state?: TState) => string;
  positionForNode: (node: Pick<TNode, "id">) => { x: number; y: number; w: number; h: number };
  onOpen: () => void;
}) {
  const position = positionForNode(node);
  const overdue = isDeadlineOverdue(state, now);
  const status = overdue ? "OVERDUE" : state?.status || "LOCKED";
  const isComplete = status === "COMPLETED";
  const isInactivePath = status === "NOT_APPLICABLE";
  const canOpen = canOpenNode(node, state, availability);
  const canAct = Boolean(availability?.canOpen) && !isComplete && !isInactivePath;
  const tone = statusTone(status);
  const style = workflowToneStyles[tone];
  const StatusIcon = workflowStatusIcons[tone];
  const NodeIcon = nodeIcons?.[node.id] || Route;
  const subtitle = nodeSubtitles?.[node.id];
  const showSubtitle = Boolean(subtitle && !isComplete && !isInactivePath);
  const summary = nodeSummary?.(node.id, state) || "";
  const className = `absolute flex flex-col justify-center rounded-xl border px-3 py-2 text-left transition-all ${
    canOpen ? "cursor-pointer hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-amber-400" : "cursor-default"
  }`;
  const styleProps = {
    left: position.x,
    top: position.y,
    width: position.w,
    height: position.h,
    borderColor: style.border,
    backgroundColor: style.bg,
    boxShadow: isInactivePath
      ? "inset 0 0 0 1px rgba(255,255,255,0.08), 0 8px 18px rgba(2,6,23,0.25)"
      : tone === "in-progress" || tone === "awaiting-approval"
        ? "0 4px 14px rgba(217,119,6,0.20)"
        : "0 1px 3px rgba(15,23,42,0.08)",
    filter: isInactivePath ? "grayscale(1)" : undefined,
  };

  const content = (
    <>
      <span className="absolute bottom-2 left-0 top-2 w-1 rounded-full" style={{ backgroundColor: style.accent }} />
      <div className={`flex items-start gap-2 pl-1.5 ${isInactivePath ? "opacity-30 blur-[1.2px]" : ""}`}>
        <NodeIcon className="mt-0.5 h-4 w-4 shrink-0" style={{ color: style.accent }} />
        <div className="min-w-0">
          <div className="whitespace-normal break-words text-[12.5px] font-semibold leading-snug" style={{ color: style.title }}>
            {node.label}
          </div>
          {showSubtitle && <div className="mt-0.5 whitespace-normal break-words text-[10.5px] leading-snug text-slate-500">{subtitle}</div>}
          {summary && <div className="mt-1 truncate text-[10.5px] font-bold leading-snug text-slate-700" title={summary}>{summary}</div>}
        </div>
      </div>
      <div className={`mt-1.5 pl-1.5 ${isInactivePath ? "opacity-30 blur-[1.2px]" : ""}`}>
        <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium leading-none" style={{ backgroundColor: style.chipBg, color: style.chipText }}>
          <StatusIcon className={`h-3 w-3 ${tone === "in-progress" ? "animate-spin" : ""}`} />
          {formatStatus(status)}
        </span>
      </div>
      {isInactivePath && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-slate-950/70">
          <span className="rounded-full border border-white/15 bg-white/10 px-2.5 py-1 text-[10px] font-black uppercase tracking-wide text-slate-200">Inactive path</span>
        </div>
      )}
      {!canOpen && availability?.disabledReason && node.clickable && !isInactivePath && (
        <div className="mt-1.5 whitespace-normal break-words pl-1.5 text-[11px] font-medium leading-tight text-slate-500">{availability.disabledReason}</div>
      )}
    </>
  );

  if (canOpen) {
    return (
      <button className={className} style={styleProps} type="button" onClick={onOpen} title={canAct ? node.label : `${node.label} output`}>
        {content}
      </button>
    );
  }

  return (
    <div className={className} style={styleProps} title={availability?.disabledReason || "Display-only step"}>
      {content}
    </div>
  );
}

function edgePath(
  fromId: string,
  toId: string,
  connectorRoutes: Record<string, WorkflowConnectorRoute>,
  anchorPoint: (nodeId: string, side: WorkflowConnectorRoute["fromSide"]) => { x: number; y: number }
) {
  const route = connectorRoutes[`${fromId}->${toId}`] || { fromSide: "right" as const, toSide: "left" as const };
  const start = anchorPoint(fromId, route.fromSide);
  const end = anchorPoint(toId, route.toSide);
  const points = route.points || defaultOrthogonalPoints(start, end, route.fromSide, route.toSide);
  return [`M ${start.x} ${start.y}`, ...points.map((point) => `L ${point.x} ${point.y}`), `L ${end.x} ${end.y}`].join(" ");
}

function defaultOrthogonalPoints(start: { x: number; y: number }, end: { x: number; y: number }, fromSide: string, toSide: string) {
  if (start.x === end.x || start.y === end.y) return [];
  if ((fromSide === "left" || fromSide === "right") && (toSide === "left" || toSide === "right")) {
    const midX = Math.round((start.x + end.x) / 2);
    return [{ x: midX, y: start.y }, { x: midX, y: end.y }];
  }
  if ((fromSide === "top" || fromSide === "bottom") && (toSide === "top" || toSide === "bottom")) {
    const midY = Math.round((start.y + end.y) / 2);
    return [{ x: start.x, y: midY }, { x: end.x, y: midY }];
  }
  return [{ x: end.x, y: start.y }];
}

function countdownPosition<TNode extends WorkflowNode>(
  nodeId: string,
  positionForNode: (node: Pick<TNode, "id">) => { x: number; y: number; w: number; h: number }
) {
  const position = positionForNode({ id: nodeId } as Pick<TNode, "id">);
  return { left: position.x, top: Math.max(8, position.y - 36) };
}
