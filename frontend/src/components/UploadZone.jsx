import { useRef, useState } from "react";

import Icon from "./Icon";

const ALLOWED = [".txt", ".md", ".pdf", ".docx"];
const MAX_BYTES = 10 * 1024 * 1024;

function problemWith(file) {
  const dot = file.name.lastIndexOf(".");
  const extension = dot === -1 ? "" : file.name.slice(dot).toLowerCase();
  if (!ALLOWED.includes(extension)) return "Use a .txt, .md, .pdf or .docx file.";
  if (file.size > MAX_BYTES) return "This file is larger than 10 MB.";
  return null;
}

export default function UploadZone({ onUpload }) {
  const [dragging, setDragging] = useState(false);
  const [items, setItems] = useState([]); // { key, name, status: "working" | "error", error }
  const inputRef = useRef(null);

  async function handleFiles(fileList) {
    const files = Array.from(fileList);
    for (const file of files) {
      const key = `${file.name}-${Date.now()}-${Math.random()}`;
      const problem = problemWith(file);
      if (problem) {
        setItems((current) => [...current, { key, name: file.name, status: "error", error: problem }]);
        continue;
      }
      setItems((current) => [...current, { key, name: file.name, status: "working" }]);
      try {
        await onUpload(file);
        setItems((current) => current.filter((item) => item.key !== key));
      } catch (error) {
        setItems((current) =>
          current.map((item) =>
            item.key === key ? { ...item, status: "error", error: error.message } : item,
          ),
        );
      }
    }
  }

  function dismiss(key) {
    setItems((current) => current.filter((item) => item.key !== key));
  }

  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={`rounded-xl border border-dashed px-4 py-5 text-center transition-colors ${
          dragging ? "border-moss bg-moss/5" : "border-ink/25 bg-surface"
        }`}
      >
        <Icon name="upload" size={22} className="mx-auto text-muted" />
        <p className="mt-2 text-[15px]">
          Drop files here or{" "}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="font-medium text-moss underline underline-offset-4 hover:text-moss-dark"
          >
            choose files
          </button>
        </p>
        <p className="mt-1 text-sm text-muted">PDF, TXT, MD or DOCX, up to 10 MB</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".txt,.md,.pdf,.docx"
          className="sr-only"
          tabIndex={-1}
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </div>

      {items.length > 0 && (
        <ul className="mt-3 space-y-2" aria-live="polite">
          {items.map((item) =>
            item.status === "working" ? (
              <li key={item.key} className="flex items-center gap-2 text-sm text-muted">
                <Icon name="spinner" size={15} className="shrink-0 animate-spin" />
                <span className="truncate">Indexing {item.name}…</span>
              </li>
            ) : (
              <li
                key={item.key}
                role="alert"
                className="rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm"
              >
                <p className="truncate font-medium">{item.name}</p>
                <p className="text-danger">{item.error}</p>
                <button
                  type="button"
                  onClick={() => dismiss(item.key)}
                  className="mt-1 text-muted underline underline-offset-4 hover:text-ink"
                >
                  Dismiss
                </button>
              </li>
            ),
          )}
        </ul>
      )}
    </div>
  );
}