import { useEffect, useRef } from "react";

import { useWorkspace } from "../workspace/WorkspaceContext";
import Icon from "./Icon";

export default function Composer({ text, setText, onOpenDocs }) {
  const { ask, asking, documents, selectedIds } = useWorkspace();
  const areaRef = useRef(null);

  useEffect(() => {
    const element = areaRef.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 160)}px`;
  }, [text]);

  useEffect(() => {
    if (!asking && window.matchMedia("(pointer: fine)").matches) {
      areaRef.current?.focus();
    }
  }, [asking]);

  async function submit() {
    const question = text.trim();
    if (!question || asking) return;
    setText("");
    const ok = await ask(question);
    if (!ok) setText(question);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  const total = documents.length;
  let label = "No documents yet";
  if (total > 0) {
    label =
      selectedIds.length === 0
        ? `Answering from all ${total} ${total === 1 ? "document" : "documents"}`
        : `Answering from ${selectedIds.length} of ${total}`;
  }

  return (
    <div className="border-t border-line bg-surface px-4 pt-3 pb-4 sm:px-8">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border border-line bg-white p-2 focus-within:border-moss focus-within:ring-2 focus-within:ring-moss/20">
          <textarea
            ref={areaRef}
            rows={1}
            maxLength={1000}
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Your question"
            placeholder="Ask about your documents"
            className="block max-h-40 w-full resize-none bg-transparent px-2 py-1.5 text-[16px] outline-none"
          />
          <div className="flex items-center justify-between gap-2 pt-1">
            <button
              type="button"
              onClick={onOpenDocs}
              className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm text-muted transition-colors hover:bg-paper hover:text-ink lg:cursor-default lg:hover:bg-transparent lg:hover:text-muted"
            >
              <Icon name="file" size={15} />
              {label}
            </button>
            <div className="flex items-center gap-3">
              {text.length > 850 && (
                <span className="text-xs text-muted">{text.length}/1000</span>
              )}
              <button
                type="button"
                onClick={submit}
                disabled={!text.trim() || asking}
                aria-label="Send question"
                className="grid h-9 w-9 place-items-center rounded-full bg-moss text-white transition-colors hover:bg-moss-dark disabled:opacity-40"
              >
                <Icon name="up" size={18} />
              </button>
            </div>
          </div>
        </div>
        <p className="mt-2 hidden text-center text-xs text-muted sm:block">
          Enter to send, Shift+Enter for a new line.
        </p>
      </div>
    </div>
  );
}