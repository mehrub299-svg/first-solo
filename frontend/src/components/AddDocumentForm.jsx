import { useState } from "react";

const MAX_TEXT = 150000;

export default function AddDocumentForm({ onSave, onClose }) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const tooLong = text.length > MAX_TEXT;
  const canSave = title.trim() !== "" && text.trim() !== "" && !tooLong && !saving;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSave) return;
    setSaving(true);
    setError("");
    try {
      await onSave(title.trim(), text.trim());
      onClose();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  const fieldClass =
    "block w-full rounded-md border border-line bg-white px-3 py-2 text-[15px] outline-none focus:border-moss focus:ring-2 focus:ring-moss/20 disabled:bg-paper";

  return (
    <form onSubmit={handleSubmit} className="border-y border-line bg-paper/60 px-5 py-4">
      <label htmlFor="doc-title" className="mb-1.5 block text-sm font-medium">
        Title
      </label>
      <input
        id="doc-title"
        type="text"
        maxLength={255}
        required
        value={title}
        disabled={saving}
        onChange={(event) => setTitle(event.target.value)}
        className={fieldClass}
      />

      <label htmlFor="doc-text" className="mt-4 mb-1.5 block text-sm font-medium">
        Text
      </label>
      <textarea
        id="doc-text"
        rows={9}
        value={text}
        disabled={saving}
        onChange={(event) => setText(event.target.value)}
        placeholder="Paste the text you want to ask questions about."
        className={`${fieldClass} resize-y leading-relaxed`}
      />
      <p className={`mt-1.5 text-sm ${tooLong ? "text-danger" : "text-muted"}`}>
        {text.length.toLocaleString()} of {MAX_TEXT.toLocaleString()} characters
      </p>

      {saving && (
        <p role="status" className="mt-3 text-sm text-muted">
          Splitting your text into passages and indexing them. This can take a few seconds.
        </p>
      )}

      {error && (
        <p
          role="alert"
          className="mt-3 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger"
        >
          {error}
        </p>
      )}

      <div className="mt-4 flex items-center gap-3">
        <button
          type="submit"
          disabled={!canSave}
          className="rounded-md bg-moss px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-moss-dark disabled:opacity-50"
        >
          {saving ? "Indexing…" : "Save document"}
        </button>
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className="rounded-md px-3 py-2 text-sm text-muted hover:text-ink disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}