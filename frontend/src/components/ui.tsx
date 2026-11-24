import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  LoaderCircle,
  X,
} from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";
export const number = (v: number | null | undefined, compact = false) =>
  v == null
    ? "—"
    : new Intl.NumberFormat("en-US", {
        notation: compact ? "compact" : "standard",
        maximumFractionDigits: compact ? 1 : 0,
      }).format(v);
export const percent = (v: number | null | undefined) =>
  v == null ? "No comparison" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
export const date = (v: string) =>
  new Date(
    v.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(v) ? v : `${v}Z`,
  ).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
const labels: Record<string, string> = {
  NORMAL: "Normal",
  ADVERTENCIA: "Warning",
  CRITICO: "Critical",
  SIN_BASE: "No baseline",
  ERROR: "Error",
  PENDING: "Pending review",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  NOT_REQUIRED: "Not required",
  WAITING_REVIEW: "Awaiting review",
  COMPLETED: "Completed",
  RUNNING: "Running",
  RESUMING: "Resuming",
};
export function Badge({ status }: { status: string | null | undefined }) {
  return (
    <span className={`badge ${(status || "").toLowerCase()}`}>
      <i />
      {labels[status || ""] || status || "Processing"}
    </span>
  );
}
export function Change({ value }: { value: number | null | undefined }) {
  return (
    <span
      className={`change ${value == null ? "muted" : value < 0 ? "negative" : "positive"}`}
    >
      {value != null &&
        (value < 0 ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />)}
      {percent(value)}
    </span>
  );
}
export function Empty({
  title = "No results yet",
  children,
}: {
  title?: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">◇</div>
      <h3>{title}</h3>
      <p>{children || "Run an analysis to see evidence and activity here."}</p>
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spin" size={22} /> Loading your workspace…
    </div>
  );
}
export function ErrorPanel({
  error,
  retry,
}: {
  error: Error | null;
  retry?: () => void;
}) {
  return (
    <div className="error-panel" role="alert">
      <AlertCircle size={20} />
      <div>
        <strong>Unable to complete this request</strong>
        <p>{error?.message}</p>
      </div>
      {retry && (
        <button className="button secondary" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}
export function Modal({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  const dialog = useRef<HTMLElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current
      ?.querySelector<HTMLElement>("button, input, select, textarea")
      ?.focus();
    return () => previous?.focus();
  }, []);
  return (
    <div className="overlay" onClick={onClose}>
      <section
        ref={dialog}
        className={`modal ${wide ? "wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
          if (e.key === "Tab") {
            const controls = Array.from(
              dialog.current?.querySelectorAll<HTMLElement>(
                "button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href]",
              ) || [],
            ).filter((element) => element.offsetParent !== null);
            const first = controls[0],
              last = controls.at(-1);
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last?.focus();
            }
            if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <header>
          <h2>{title}</h2>
          <button
            className="icon-button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
