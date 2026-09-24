import { FormEvent, useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import Modal from "./Modal";

export interface FormField {
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  hint?: string;
}

interface FormModalProps {
  open: boolean;
  title: string;
  description?: string;
  fields: FormField[];
  submitLabel: string;
  onSubmit: (values: Record<string, string>) => Promise<unknown>;
  onClose: () => void;
}

export default function FormModal({ open, title, description, fields, submitLabel, onSubmit, onClose }: FormModalProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) { setValues({}); setError(null); }
  }, [open]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const trimmed = Object.fromEntries(Object.entries(values).map(([k, v]) => [k, v.trim()]).filter(([, v]) => v));
      await onSubmit(trimmed);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "No se pudo guardar. Intenta de nuevo.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={saving ? () => {} : onClose}>
      <form onSubmit={handleSubmit} className="p-6">
        <div className="flex items-start justify-between mb-1">
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="text-gray-400 hover:text-gray-600 ml-4 shrink-0 transition-colors active:scale-90"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {description && <p className="text-sm text-gray-500 mb-5">{description}</p>}

        <div className="space-y-4">
          {fields.map((f, i) => (
            <div key={f.name}>
              <label htmlFor={`fm-${f.name}`} className="text-xs font-medium text-gray-500">
                {f.label}{!f.required && <span className="text-gray-400 font-normal"> (opcional)</span>}
              </label>
              <input
                id={`fm-${f.name}`}
                autoFocus={i === 0}
                required={f.required}
                value={values[f.name] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                placeholder={f.placeholder}
                className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500"
              />
              {f.hint && <p className="mt-1 text-xs text-gray-400">{f.hint}</p>}
            </div>
          ))}
        </div>

        {error && <p role="alert" className="mt-4 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors active:scale-[0.97] disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded-lg hover:opacity-90 transition-transform active:scale-[0.97] disabled:opacity-60"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            {submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
}
