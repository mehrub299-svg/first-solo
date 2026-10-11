import { useState } from "react";

import { useWorkspace } from "../workspace/WorkspaceContext";
import AddDocumentForm from "./AddDocumentForm";
import DocumentRow from "./DocumentRow";
import Icon from "./Icon";
import UploadZone from "./UploadZone";

export default function DocumentsPanel({ open, onClose }) {
  const {
    documents,
    documentsLoading,
    documentsError,
    selectedIds,
    toggleDocument,
    selectAllDocuments,
    clearSelection,
    addTextDocument,
    uploadFile,
    removeDocument,
  } = useWorkspace();
  const [pasting, setPasting] = useState(false);

  const selectedCount = selectedIds.length;
  let summary = "No documents yet";
  if (documents.length > 0) {
    summary = selectedCount === 0 ? "Searching all documents" : `${selectedCount} selected`;
  }

  return (
    <aside
      aria-label="Documents"
      className={`fixed inset-y-0 right-0 z-30 flex w-[92%] max-w-[360px] flex-col border-l border-line bg-paper transition-transform duration-200 lg:static lg:z-auto lg:w-[340px] lg:max-w-none lg:translate-x-0 ${
        open ? "translate-x-0" : "translate-x-full"
      }`}
    >
      <div className="flex items-center justify-between px-4 pt-5 pb-3">
        <h2 className="font-serif text-xl font-medium tracking-tight">Documents</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close documents"
          className="rounded-md p-1.5 text-muted hover:bg-paper-deep hover:text-ink lg:hidden"
        >
          <Icon name="close" />
        </button>
      </div>

      <div className="space-y-3 px-4 pb-4">
        <UploadZone onUpload={uploadFile} />
        {pasting ? (
          <div className="-mx-4">
            <AddDocumentForm onSave={addTextDocument} onClose={() => setPasting(false)} />
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setPasting(true)}
            className="text-sm font-medium text-moss underline underline-offset-4 hover:text-moss-dark"
          >
            Paste text instead
          </button>
        )}
      </div>

      <div className="flex items-center justify-between border-y border-line bg-paper-deep/60 px-4 py-2 text-sm">
        <span className="text-muted">{summary}</span>
        {documents.length > 0 && (
          <span className="flex gap-3">
            <button
              type="button"
              onClick={selectAllDocuments}
              className="font-medium text-moss hover:text-moss-dark"
            >
              Select all
            </button>
            <button
              type="button"
              onClick={clearSelection}
              disabled={selectedCount === 0}
              className="font-medium text-moss hover:text-moss-dark disabled:text-muted disabled:opacity-60"
            >
              Clear
            </button>
          </span>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {documentsLoading && <p className="px-4 py-6 text-sm text-muted">Loading documents…</p>}

        {!documentsLoading && documentsError && (
          <p role="alert" className="px-4 py-6 text-sm text-danger">
            {documentsError}
          </p>
        )}

        {!documentsLoading && !documentsError && documents.length === 0 && (
          <div className="px-4 py-8">
            <p className="font-serif text-lg">Nothing here yet.</p>
            <p className="mt-1 text-sm text-muted">
              Upload a file or paste some text. Then tick documents to limit answers to them.
            </p>
          </div>
        )}

        <ul className="divide-y divide-line">
          {documents.map((item) => (
            <DocumentRow
              key={item.id}
              item={item}
              checked={selectedIds.includes(item.id)}
              onToggle={toggleDocument}
              onDelete={removeDocument}
            />
          ))}
        </ul>
      </div>
    </aside>
  );
}