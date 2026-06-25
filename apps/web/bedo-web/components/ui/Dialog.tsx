"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

const focusableSelectors = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

type DialogProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  labelledBy?: string;
  size?: "sm" | "md" | "lg" | "xl";
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  context?: ReactNode;
  initialFocus?: "close" | "content";
};

const widthBySize = {
  sm: "max-w-md",
  md: "max-w-xl",
  lg: "max-w-2xl",
  xl: "max-w-3xl",
};

export function Dialog({
  title,
  eyebrow,
  description,
  labelledBy,
  size = "md",
  onClose,
  children,
  footer,
  context,
  initialFocus = "close",
}: DialogProps) {
  const [mounted, setMounted] = useState(false);
  const generatedTitleId = useId();
  const titleId = labelledBy || generatedTitleId;
  const closeRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    previouslyFocused.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    if (initialFocus === "content") {
      panelRef.current?.focus();
    } else {
      closeRef.current?.focus();
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key === "Tab") {
        trapFocus(event);
      }
    }

    function trapFocus(event: KeyboardEvent) {
      const focusable = Array.from(panelRef.current?.querySelectorAll<HTMLElement>(focusableSelectors) || []).filter(
        (element) => element.offsetParent !== null || element === document.activeElement,
      );
      if (!focusable.length) {
        event.preventDefault();
        panelRef.current?.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused.current?.focus();
    };
  }, [initialFocus, mounted, onClose]);

  if (!mounted) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/55 p-4"
      data-dialog-backdrop
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`relative z-10 flex max-h-[92vh] w-full ${widthBySize[size]} flex-col rounded-lg border border-slate-200 bg-white shadow-2xl outline-none`}
      >
        <div className="border-b border-slate-200 px-5 py-4 sm:px-6 sm:py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              {eyebrow && <div className="text-xs font-black uppercase tracking-wide text-slate-500">{eyebrow}</div>}
              <h2 id={titleId} className="mt-1 text-xl font-black text-slate-950">{title}</h2>
              {description && <p className="mt-1 text-sm font-semibold leading-6 text-slate-600">{description}</p>}
            </div>
            <button ref={closeRef} className="focus-ring rounded-md p-2 text-slate-500 hover:bg-slate-100" type="button" onClick={onClose} aria-label="Close">
              <X className="h-5 w-5" />
            </button>
          </div>
          {context && <div className="mt-4">{context}</div>}
        </div>
        <div className="min-h-0 overflow-y-auto px-5 py-4 sm:px-6 sm:py-5">{children}</div>
        {footer && <div className="flex flex-wrap justify-end gap-3 border-t border-slate-200 px-5 py-4 sm:px-6">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
