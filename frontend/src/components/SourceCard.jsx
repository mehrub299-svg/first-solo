import { useMemo } from "react";

import { highlightSegments } from "../lib/answer";

export default function SourceCard({ idPrefix, number, source, answer, active, highlight }) {
  const segments = useMemo(
    () =>
      highlight
        ? highlightSegments(source.content, answer)
        : [{ text: source.content, mark: false }],
    [highlight, source.content, answer],
  );

  return (
    <li
      id={`source-${idPrefix}-${number}`}
      className={`rounded-xl border p-4 transition-colors ${
        active ? "border-ink bg-white" : "border-line bg-paper/60"
      }`}
    >
      <div className="flex items-center gap-2.5">
        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded bg-ink px-1 text-[11px] font-medium text-surface">
          {number}
        </span>
        <p className="min-w-0 truncate font-medium" title={source.document_title}>
          {source.document_title}
        </p>
      </div>

      <p className="mt-3 font-serif text-[15.5px] leading-relaxed whitespace-pre-line text-ink/85">
        {segments.map((segment, index) =>
          segment.mark ? (
            <mark key={index} className="sweep">
              {segment.text}
            </mark>
          ) : (
            <span key={index}>{segment.text}</span>
          ),
        )}
      </p>
    </li>
  );
}