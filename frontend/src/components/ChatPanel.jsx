import { useEffect, useRef, useState } from "react";

import { useWorkspace } from "../workspace/WorkspaceContext";
import Composer from "./Composer";
import Icon from "./Icon";
import { AssistantMessage, PendingMessage, UserMessage } from "./Messages";

function EmptyState({ hasDocuments, onOpenDocs }) {
  return (
    <div className="pt-[12vh]">
      <h2 className="font-serif text-4xl leading-tight font-medium tracking-tight">
        {hasDocuments ? "What do you want to know?" : "Start with a document."}
      </h2>
      {hasDocuments ? (
        <div className="mt-3 max-w-lg space-y-3 text-muted">
          <p>
            Ask about something specific: a name, a date, an amount, a clause. Each answer
            shows the passages it came from.
          </p>
          <p>
            Broad requests like "summarize everything" don't work well yet, because an answer
            is built from the few passages that best match your question. Tick a document on
            the right to answer only from it.
          </p>
        </div>
      ) : (
        <>
          <p className="mt-3 max-w-md text-muted">
            Upload a PDF or a text file, or paste some notes, in the documents panel. Then ask
            about them here.
          </p>
          <button
            type="button"
            onClick={onOpenDocs}
            className="mt-6 rounded-lg bg-moss px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-moss-dark lg:hidden"
          >
            Open documents
          </button>
        </>
      )}
    </div>
  );
}

export default function ChatPanel({ onOpenChats, onOpenDocs }) {
  const {
    activeChatId,
    chats,
    messages,
    messagesLoading,
    asking,
    pendingQuestion,
    askError,
    documents,
    documentsLoading,
  } = useWorkspace();
  const [text, setText] = useState("");
  const anchorRef = useRef(null);
  const endRef = useRef(null);

  const title = chats.find((chat) => chat.id === activeChatId)?.title ?? "New chat";
  const lastUserIndex = messages.findLastIndex((message) => message.role === "user");
  const showEmpty = messages.length === 0 && !asking && !messagesLoading;

  // After a new exchange or an opened chat, show the last question at the top.
  useEffect(() => {
    anchorRef.current?.scrollIntoView({ block: "start" });
  }, [messages.length, activeChatId]);

  useEffect(() => {
    if (asking) endRef.current?.scrollIntoView({ block: "end" });
  }, [asking]);

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-surface">
      <header className="flex items-center gap-2 border-b border-line px-3 py-2.5 sm:px-5">
        <button
          type="button"
          onClick={onOpenChats}
          aria-label="Open chats"
          className="rounded-md p-2 text-muted hover:bg-paper hover:text-ink lg:hidden"
        >
          <Icon name="menu" />
        </button>
        <h1 className="min-w-0 flex-1 truncate font-serif text-lg font-medium" title={title}>
          {title}
        </h1>
        <button
          type="button"
          onClick={onOpenDocs}
          aria-label="Open documents"
          className="rounded-md p-2 text-muted hover:bg-paper hover:text-ink lg:hidden"
        >
          <Icon name="file" />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 pb-6 sm:px-8">
          {messagesLoading && (
            <div className="space-y-3 pt-10" aria-hidden="true">
              <div className="ml-auto h-10 w-2/5 animate-pulse rounded-2xl bg-line/50" />
              <div className="h-4 w-full animate-pulse rounded bg-line/50" />
              <div className="h-4 w-4/5 animate-pulse rounded bg-line/50" />
            </div>
          )}

          {showEmpty && !documentsLoading && (
            <EmptyState hasDocuments={documents.length > 0} onOpenDocs={onOpenDocs} />
          )}

          {messages.map((message, index) => (
            <div
              key={message.id}
              ref={index === lastUserIndex ? anchorRef : null}
              className="scroll-mt-4"
            >
              {message.role === "user" ? (
                <UserMessage content={message.content} />
              ) : (
                <AssistantMessage message={message} isLatest={index === messages.length - 1} />
              )}
            </div>
          ))}

          {asking && <PendingMessage question={pendingQuestion} />}

          {askError && (
            <p
              role="alert"
              className="mt-6 rounded-md border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger"
            >
              {askError}
            </p>
          )}

          <div ref={endRef} />
        </div>
      </div>

      <Composer text={text} setText={setText} onOpenDocs={onOpenDocs} />
    </main>
  );
}