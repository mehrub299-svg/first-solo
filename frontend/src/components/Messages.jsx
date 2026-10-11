import { Fragment, useState } from "react";

import { isNoAnswer } from "../lib/answer";
import Icon from "./Icon";
import SourceCard from "./SourceCard";

const CITATION = /(\[\d+(?:\s*,\s*\d+)*\])/;
const CITATION_ONLY = /^\[(\d+(?:\s*,\s*\d+)*)\]$/;

function CiteChip({ number, active, onPick }) {
  return (
    <button
      type="button"
      onClick={() => onPick(number)}
      aria-label={`Show source ${number}`}
      className={`mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded px-1 align-middle font-sans text-[11px] font-medium text-surface transition-colors ${
        active ? "bg-moss" : "bg-ink hover:bg-moss"
      }`}
    >
      {number}
    </button>
  );
}

function renderAnswer(text, sourceCount, activeSource, onPick) {
  return text
    .replace(/\*\*/g, "")
    .split(CITATION)
    .map((part, index) => {
      const match = part.match(CITATION_ONLY);
      if (!match) return <Fragment key={index}>{part}</Fragment>;

      const numbers = match[1].split(",").map((value) => Number(value.trim()));
      if (numbers.some((n) => n < 1 || n > sourceCount)) {
        return <Fragment key={index}>{part}</Fragment>;
      }
      return (
        <Fragment key={index}>
          {numbers.map((n) => (
            <CiteChip key={n} number={n} active={activeSource === n} onPick={onPick} />
          ))}
        </Fragment>
      );
    });
}

export function UserMessage({ content }) {
  return (
    <div className="flex justify-end pt-8">
      <p className="max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-[15.5px] leading-relaxed whitespace-pre-wrap text-surface">
        {content}
      </p>
    </div>
  );
}

export function PendingMessage({ question }) {
  return (
    <>
      <UserMessage content={question} />
      <div role="status" className="flex items-center gap-3 py-6 text-muted">
        <span className="flex gap-1" aria-hidden="true">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </span>
        <span className="text-sm">Searching your documents</span>
      </div>
    </>
  );
}

export function AssistantMessage({ message, isLatest }) {
  const sources = message.sources ?? [];
  const noAnswer = isNoAnswer(message.content);
  const [open, setOpen] = useState(isLatest);
  const [active, setActive] = useState(null);
  const [copied, setCopied] = useState(false);

  function pick(number) {
    setOpen(true);
    setActive(number);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    requestAnimationFrame(() => {
      document
        .getElementById(`source-${message.id}-${number}`)
        ?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "nearest" });
    });
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard not available: nothing to do.
    }
  }

  const buttonClass =
    "inline-flex items-center gap-1 rounded-md px-2 py-1 transition-colors hover:bg-paper hover:text-ink";

  return (
    <article className="py-6">
      <div className="font-serif text-[1.2rem] leading-[1.6] whitespace-pre-wrap">
        {renderAnswer(message.content, noAnswer ? 0 : sources.length, active, pick)}
      </div>

      <div className="mt-3 flex items-center gap-1 text-sm text-muted">
        {sources.length > 0 && (
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            className={buttonClass}
          >
            {noAnswer ? "Closest passages" : "Sources"} ({sources.length})
            <Icon
              name="chevron"
              size={15}
              className={`transition-transform ${open ? "rotate-180" : ""}`}
            />
          </button>
        )}
        <button type="button" onClick={copy} className={buttonClass}>
          <Icon name={copied ? "check" : "copy"} size={15} />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {open && sources.length > 0 && (
        <div className="mt-3">
          {noAnswer && (
            <p className="mb-3 text-sm text-muted">
              None of these answered the question, so nothing is highlighted.
            </p>
          )}
          <ol className="space-y-3">
            {sources.map((source, index) => (
              <SourceCard
                key={`${source.document_id}-${source.chunk_index}`}
                idPrefix={message.id}
                number={index + 1}
                source={source}
                answer={message.content}
                active={active === index + 1}
                highlight={!noAnswer}
              />
            ))}
          </ol>
        </div>
      )}
    </article>
  );
}