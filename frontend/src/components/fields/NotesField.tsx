import { Check, Loader2, Pencil, X } from "lucide-react";
import { useRef, useState } from "react";
import { updateNotes } from "../../api/databases";
import type { FieldRendererProps } from "./types";

export function NotesField({ record }: FieldRendererProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(record.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function startEdit() {
    setDraft(record.notes ?? "");
    setEditing(true);
    setError(null);
    setTimeout(() => textareaRef.current?.focus(), 0);
  }

  function cancel() {
    setEditing(false);
    setError(null);
  }

  async function save() {
    if (draft === (record.notes ?? "")) {
      setEditing(false);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateNotes(record.id, draft);
      record.notes = draft;
      setEditing(false);
    } catch {
      setError("Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (editing) {
    return (
      <div className="flex flex-col gap-1 min-w-[180px]">
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={3}
          className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          placeholder="Add a note…"
        />
        <div className="flex items-center gap-1">
          <button
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-0.5 text-xs text-green-700 hover:text-green-900 disabled:opacity-50"
            title="Save"
          >
            {saving ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Check className="w-3 h-3" />
            )}
            Save
          </button>
          <button
            onClick={cancel}
            disabled={saving}
            className="inline-flex items-center gap-0.5 text-xs text-gray-400 hover:text-gray-600 disabled:opacity-50"
            title="Cancel"
          >
            <X className="w-3 h-3" />
            Cancel
          </button>
        </div>
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  return (
    <div
      className="group flex items-start gap-1 cursor-pointer min-w-[120px]"
      onClick={startEdit}
      title="Click to edit notes"
    >
      {record.notes ? (
        <span className="text-sm text-gray-700 whitespace-pre-wrap break-words max-w-[240px]">
          {record.notes}
        </span>
      ) : (
        <span className="text-sm text-gray-300 italic">Add note…</span>
      )}
      <Pencil className="w-3 h-3 mt-0.5 text-gray-300 group-hover:text-gray-500 flex-shrink-0 transition-colors" />
    </div>
  );
}
