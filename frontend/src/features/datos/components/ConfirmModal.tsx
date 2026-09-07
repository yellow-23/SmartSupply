import { X } from "lucide-react";
import Modal from "../../../shared/ui/Modal";

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirmClassName?: string;
  isLoading?: boolean;
  onConfirm?: () => void;
  onClose: () => void;
}

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = "Confirmar",
  confirmClassName = "bg-primary text-white hover:opacity-90",
  isLoading = false,
  onConfirm,
  onClose,
}: ConfirmModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose}>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 ml-4 shrink-0 transition-colors active:scale-90"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <p className="text-sm text-gray-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors active:scale-[0.97]"
          >
            {onConfirm ? "Cancelar" : "Cerrar"}
          </button>
          {onConfirm && (
            <button
              onClick={onConfirm}
              disabled={isLoading}
              className={`px-4 py-2 text-sm rounded-lg font-medium disabled:opacity-60 transition-transform active:scale-[0.97] ${confirmClassName}`}
            >
              {isLoading ? "Procesando…" : confirmLabel}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
