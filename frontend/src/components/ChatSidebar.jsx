import { useState } from "react";

import { useAuth } from "../auth/AuthContext";
import { groupChatsByDay } from "../lib/format";
import { useWorkspace } from "../workspace/WorkspaceContext";
import Icon from "./Icon";
import Wordmark from "./Wordmark";

function ChatItem({ chat, active, disabled, onOpen, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleDelete() {
    setBusy(true);
    setError("");
    try {
      await onDelete(chat.id);
    } catch (err) {
      setError(err.message);
      setBusy(false);
      setConfirming(false);
    }
  }

  if (confirming) {
    return (
      <li className="rounded-lg border border-danger/30 bg-danger/5 p-3">
        <p className="text-sm">Delete this chat and its messages?</p>
        <div className="mt-2.5 flex gap-2">
          <button
            type="button"
            onClick={handleDelete}
            disabled={busy}
            className="rounded-md bg-danger px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            {busy ? "Deleting…" : "Delete chat"}
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
      </li>
    );
  }

  return (
    <li className="group relative">
      {active && <span className="absolute top-2 bottom-2 left-0 w-1 rounded-full bg-mark" />}
      <button
        type="button"
        onClick={() => onOpen(chat.id)}
        disabled={disabled}
        aria-current={active ? "true" : undefined}
        title={chat.title}
        className={`block w-full truncate rounded-lg py-2 pr-9 pl-4 text-left text-[14.5px] transition-colors disabled:opacity-60 ${
          active ? "bg-surface font-medium" : "hover:bg-paper"
        }`}
      >
        {chat.title}
      </button>
      <button
        type="button"
        onClick={() => setConfirming(true)}
        aria-label={`Delete chat ${chat.title}`}
        className="absolute top-1/2 right-1.5 -translate-y-1/2 rounded p-1.5 text-muted transition-opacity hover:text-danger focus-visible:opacity-100 lg:opacity-0 lg:group-hover:opacity-100"
      >
        <Icon name="trash" size={15} />
      </button>
      {error && (
        <p role="alert" className="px-4 pb-1 text-xs text-danger">
          {error}
        </p>
      )}
    </li>
  );
}

export default function ChatSidebar({ open, onClose }) {
  const { user, signOut } = useAuth();
  const { chats, chatsLoading, chatsError, activeChatId, asking, openChat, removeChat } =
    useWorkspace();
  const groups = groupChatsByDay(chats);

  function handleNewChat() {
    openChat(null);
    onClose();
  }

  function handleOpen(id) {
    openChat(id);
    onClose();
  }

  return (
    <aside
      aria-label="Chats"
      className={`fixed inset-y-0 left-0 z-30 flex w-[88%] max-w-[300px] flex-col border-r border-line bg-paper-deep transition-transform duration-200 lg:static lg:z-auto lg:w-[280px] lg:max-w-none lg:translate-x-0 ${
        open ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="flex items-center justify-between px-4 pt-5 pb-4">
        <Wordmark spinning={asking} />
        <button
          type="button"
          onClick={onClose}
          aria-label="Close chats"
          className="rounded-md p-1.5 text-muted hover:bg-paper hover:text-ink lg:hidden"
        >
          <Icon name="close" />
        </button>
      </div>

      <div className="px-3 pb-2">
        <button
          type="button"
          onClick={handleNewChat}
          disabled={asking}
          className="flex w-full items-center gap-2 rounded-lg bg-ink px-3 py-2.5 text-[15px] font-medium text-surface transition-colors hover:bg-ink-soft disabled:opacity-50"
        >
          <Icon name="plus" size={17} />
          New chat
        </button>
      </div>

      <nav aria-label="Chat history" className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {chatsLoading && (
          <div className="space-y-2 px-1 pt-3" aria-hidden="true">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="h-8 animate-pulse rounded-lg bg-line/50" />
            ))}
          </div>
        )}

        {chatsError && (
          <p role="alert" className="px-3 py-4 text-sm text-danger">
            {chatsError}
          </p>
        )}

        {!chatsLoading && !chatsError && chats.length === 0 && (
          <p className="px-3 py-4 text-sm text-muted">Your chats will appear here.</p>
        )}

        {groups.map((group) => (
          <section key={group.label}>
            <h3 className="px-3 pt-4 pb-1.5 text-sm text-muted">{group.label}</h3>
            <ul className="space-y-0.5">
              {group.items.map((chat) => (
                <ChatItem
                  key={chat.id}
                  chat={chat}
                  active={chat.id === activeChatId}
                  disabled={asking}
                  onOpen={handleOpen}
                  onDelete={removeChat}
                />
              ))}
            </ul>
          </section>
        ))}
      </nav>

      <div className="flex items-center gap-3 border-t border-line px-4 py-3">
        <span
          className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-mark font-medium text-ink"
          aria-hidden="true"
        >
          {user.email[0].toUpperCase()}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm" title={user.email}>
          {user.email}
        </span>
        <button
          type="button"
          onClick={signOut}
          aria-label="Sign out"
          title="Sign out"
          className="rounded-md p-1.5 text-muted transition-colors hover:bg-paper hover:text-ink"
        >
          <Icon name="logout" />
        </button>
      </div>
    </aside>
  );
}