import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { askQuestion } from "../api/chat";
import { deleteChat, listChats, listMessages } from "../api/chats";
import {
  createDocument,
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "../api/documents";
import { useAuth } from "../auth/AuthContext";

const WorkspaceContext = createContext(null);
const NEW_CHAT = "new";

function loadSelections(storageKey) {
  try {
    return JSON.parse(localStorage.getItem(storageKey)) ?? {};
  } catch {
    return {};
  }
}

export function WorkspaceProvider({ children }) {
  const { user } = useAuth();
  const storageKey = `p101_selection_${user.id}`;

  const [chats, setChats] = useState([]);
  const [chatsLoading, setChatsLoading] = useState(true);
  const [chatsError, setChatsError] = useState("");
  const [activeChatId, setActiveChatId] = useState(null); // null = a new, unsaved chat
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState("");
  const [askError, setAskError] = useState("");
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState("");
  const [selections, setSelections] = useState(() => loadSelections(storageKey));

  const activeRef = useRef(null);
  const askingRef = useRef(false);

  const selectionKey = activeChatId === null ? NEW_CHAT : String(activeChatId);
  const selectionKeyRef = useRef(selectionKey);
  useEffect(() => {
    selectionKeyRef.current = selectionKey;
  }, [selectionKey]);

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(selections));
  }, [selections, storageKey]);

  useEffect(() => {
    let cancelled = false;
    listChats()
      .then((items) => {
        if (!cancelled) setChats(items);
      })
      .catch((error) => {
        if (!cancelled) setChatsError(error.message);
      })
      .finally(() => {
        if (!cancelled) setChatsLoading(false);
      });
    listDocuments()
      .then((items) => {
        if (!cancelled) setDocuments(items);
      })
      .catch((error) => {
        if (!cancelled) setDocumentsError(error.message);
      })
      .finally(() => {
        if (!cancelled) setDocumentsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Selected documents for the open chat. Deleted documents drop out silently.
  const selectedIds = useMemo(() => {
    const stored = selections[selectionKey] ?? [];
    return stored.filter((id) => documents.some((doc) => doc.id === id));
  }, [selections, selectionKey, documents]);

  const refreshChats = useCallback(async () => {
    try {
      setChats(await listChats());
    } catch {
      // Keep the list we already have.
    }
  }, []);

  const openChat = useCallback(async (id) => {
    if (askingRef.current) return;
    activeRef.current = id;
    setActiveChatId(id);
    setAskError("");
    setMessages([]);
    if (id === null) {
      setMessagesLoading(false);
      return;
    }
    setMessagesLoading(true);
    try {
      const items = await listMessages(id);
      if (activeRef.current === id) setMessages(items);
    } catch (error) {
      if (activeRef.current === id) setAskError(error.message);
    } finally {
      if (activeRef.current === id) setMessagesLoading(false);
    }
  }, []);

  const removeChat = useCallback(
    async (id) => {
      await deleteChat(id);
      setChats((current) => current.filter((chat) => chat.id !== id));
      setSelections((current) => {
        const { [String(id)]: _removed, ...rest } = current;
        return rest;
      });
      if (activeRef.current === id) openChat(null);
    },
    [openChat],
  );

  const ask = useCallback(
    async (question) => {
      if (askingRef.current) return false;
      askingRef.current = true;
      setAsking(true);
      setPendingQuestion(question);
      setAskError("");
      try {
        const result = await askQuestion({
          question,
          documentIds: selectedIds,
          chatId: activeChatId,
        });
        const now = new Date().toISOString();
        const stamp = Date.now();
        setMessages((current) => [
          ...current,
          { id: `local-${stamp}-u`, role: "user", content: question, sources: null, created_at: now },
          { id: `local-${stamp}-a`, role: "assistant", content: result.answer, sources: result.sources, created_at: now },
        ]);
        if (activeChatId === null) {
          activeRef.current = result.chat_id;
          setActiveChatId(result.chat_id);
          // The new chat inherits the selection made on the blank chat.
          setSelections((current) => ({
            ...current,
            [String(result.chat_id)]: current[NEW_CHAT] ?? [],
            [NEW_CHAT]: [],
          }));
        }
        refreshChats();
        return true;
      } catch (error) {
        setAskError(error.message);
        return false;
      } finally {
        askingRef.current = false;
        setAsking(false);
        setPendingQuestion("");
      }
    },
    [selectedIds, activeChatId, refreshChats],
  );

  const toggleDocument = useCallback(
    (id) => {
      setSelections((current) => {
        const existing = current[selectionKey] ?? [];
        const next = existing.includes(id)
          ? existing.filter((value) => value !== id)
          : [...existing, id];
        return { ...current, [selectionKey]: next };
      });
    },
    [selectionKey],
  );

  const selectAllDocuments = useCallback(() => {
    setSelections((current) => ({
      ...current,
      [selectionKey]: documents.map((doc) => doc.id),
    }));
  }, [selectionKey, documents]);

  const clearSelection = useCallback(() => {
    setSelections((current) => ({ ...current, [selectionKey]: [] }));
  }, [selectionKey]);

  const registerDocument = useCallback((created) => {
    setDocuments((current) => [created, ...current]);
    // If you are already picking documents, a new one joins the pick.
    setSelections((current) => {
      const key = selectionKeyRef.current;
      const existing = current[key] ?? [];
      return existing.length > 0 ? { ...current, [key]: [...existing, created.id] } : current;
    });
  }, []);

  const addTextDocument = useCallback(
    async (title, text) => {
      const created = await createDocument(title, text);
      registerDocument(created);
      return created;
    },
    [registerDocument],
  );

  const uploadFile = useCallback(
    async (file) => {
      const created = await uploadDocument(file);
      registerDocument(created);
      return created;
    },
    [registerDocument],
  );

  const removeDocument = useCallback(async (id) => {
    await deleteDocument(id);
    setDocuments((current) => current.filter((doc) => doc.id !== id));
  }, []);

  const value = {
    chats, chatsLoading, chatsError, activeChatId, openChat, removeChat,
    messages, messagesLoading, asking, pendingQuestion, askError, ask,
    documents, documentsLoading, documentsError, selectedIds,
    toggleDocument, selectAllDocuments, clearSelection,
    addTextDocument, uploadFile, removeDocument,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used inside WorkspaceProvider");
  return context;
}