import { useState } from "react";

import { formatDate } from "../lib/format";
import Icon from "./Icon";

export default function DocumentRow({ item, checked, onToggle, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const passages = `${item.chunk_count} ${item.chunk_count === 1 ? "passage" : "passages"}`;

  async function handleDelete() {
    setBusy(true);
    setError("");
    try {
      await onDelete(item.id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
      setConfirming(false);
    }
  }

  return (
    <li className={`px-4 py-3 transition-colors ${checked ? "bg-surface" : ""}`}>
      <div className="flex items-start gap-3">
        <input
          id={`doc-${item.id}`}
          type="checkbox"
          checked={checked}
          onChange={() => onToggle(item.id)}
          className="mt-1.5 h-4 w-4 shrink-0 accent-moss"
        />
        <label htmlFor={`doc-${item.id}`} className="min-w-0 flex-1 cursor-pointer">
          <span className="block truncate font-serif text-[16px] font-medium" title={item.title}>
            {item.title}
          </span>
          <span className="mt-0.5 block text-sm text-muted">
            {passages}, added {formatDate(item.created_at)}
          </span>
        </label>
        {!confirming && (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            aria-label={`Delete ${item.title}`}
            className="shrink-0 rounded p-1.5 text-muted transition-colors hover:text-danger"
          >
            <Icon name="trash" size={16} />
          </button>
        )}
      </div>

      {confirming && (
        <div className="mt-3 rounded-md border border-danger/30 bg-danger/5 p-3">
          <p className="text-sm">Delete this document and its passages? This can't be undone.</p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={handleDelete}
              disabled={busy}
              className="rounded-md bg-danger px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
            >
              {busy ? "Deleting…" : "Delete document"}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={busy}
              className="rounded-md px-3 py-1.5 text-sm text-muted hover:text-ink"
            >
              Keep
            </button>
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {error}
        </p>
      )}
    </li>
  );
}