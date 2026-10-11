import { useEffect, useState } from "react";

import ChatPanel from "../components/ChatPanel";
import ChatSidebar from "../components/ChatSidebar";
import DocumentsPanel from "../components/DocumentsPanel";

export default function HomePage() {
  const [chatsOpen, setChatsOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);

  useEffect(() => {
    function handleKey(event) {
      if (event.key === "Escape") {
        setChatsOpen(false);
        setDocsOpen(false);
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const closeAll = () => {
    setChatsOpen(false);
    setDocsOpen(false);
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-paper">
      <ChatSidebar open={chatsOpen} onClose={() => setChatsOpen(false)} />
      <ChatPanel
        onOpenChats={() => setChatsOpen(true)}
        onOpenDocs={() => setDocsOpen(true)}
      />
      <DocumentsPanel open={docsOpen} onClose={() => setDocsOpen(false)} />

      {(chatsOpen || docsOpen) && (
        <button
          type="button"
          aria-label="Close panel"
          onClick={closeAll}
          className="fixed inset-0 z-20 bg-ink/30 lg:hidden"
        />
      )}
    </div>
  );
}