import { cn } from "../../../shared/lib/utils";

type Status = "Alerta" | "Normal" | "Exceso" | "Pendiente" | "Aprobada" | "Rechazada" | "Activo" | "Inactivo" | "OK" | "Revisar";

const styles: Record<Status, string> = {
  Alerta:    "bg-red-100 text-red-700 border border-red-200",
  Normal:    "bg-green-100 text-green-700 border border-green-200",
  Exceso:    "bg-orange-100 text-orange-700 border border-orange-200",
  Pendiente: "bg-orange-100 text-orange-700 border border-orange-200",
  Aprobada:  "bg-green-100 text-green-700 border border-green-200",
  Rechazada: "bg-red-100 text-red-700 border border-red-200",
  Activo:    "bg-green-100 text-green-700 border border-green-200",
  Inactivo:  "bg-gray-100 text-gray-500 border border-gray-200",
  OK:        "bg-green-100 text-green-700 border border-green-200",
  Revisar:   "bg-orange-100 text-orange-700 border border-orange-200",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", styles[status])}>
      {status}
    </span>
  );
}
