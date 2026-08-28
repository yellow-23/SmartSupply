import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Database, ChevronDown, ChevronRight, RotateCcw, Trash2, Loader2, Sparkles,
  Layers, CheckCircle2, FileSpreadsheet,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  listBusinesses, listBusinessStores, listIngests, getIngestRecords,
  revertIngest, deleteIngest, updateRecord, deleteRecord, IngestLogItem,
} from "../../../shared/api/data";
import { chatIngest } from "../../ingest/api/ingest";
import { StatusBadge } from "../components/StatusBadge";
import ConfirmModal from "../components/ConfirmModal";

type Confirm =
  | { type: "revert"; log: IngestLogItem }
  | { type: "delete"; log: IngestLogItem }
  | null;

export default function Datos() {
  const qc = useQueryClient();
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [storeNbr, setStoreNbr] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<Confirm>(null);

  const businesses = useQuery({ queryKey: ["businesses"], queryFn: listBusinesses });

  const stores = useQuery({
    queryKey: ["stores", businessId],
    queryFn: () => listBusinessStores(businessId!),
    enabled: businessId != null,
  });

  const ingests = useQuery({
    queryKey: ["ingests", businessId, storeNbr],
    queryFn: () => listIngests(businessId!, storeNbr ?? undefined),
    enabled: businessId != null,
  });

  const revertMut = useMutation({
    mutationFn: (id: number) => revertIngest(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ingests"] }); setConfirm(null); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteIngest(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ingests"] }); setConfirm(null); },
  });

  const loads = ingests.data ?? [];
  const activeLoads = loads.filter(l => l.status === "active");
  const totalRecords = activeLoads.reduce((acc, l) => acc + l.records_loaded, 0);

  const summary = [
    { label: "Cargas totales", value: String(loads.length), icon: FileSpreadsheet, bg: "bg-blue-50", text: "text-blue-900" },
    { label: "Cargas activas", value: String(activeLoads.length), icon: CheckCircle2, bg: "bg-emerald-50", text: "text-emerald-500" },
    { label: "Registros activos", value: totalRecords.toLocaleString("es-CL"), icon: Layers, bg: "bg-indigo-50", text: "text-indigo-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="space-y-1">
        <div className="flex items-center gap-2">
          <Database className="w-6 h-6 text-indigo-600" />
          <h1 className="text-2xl font-bold text-gray-900">Datos</h1>
        </div>
        <p className="text-sm text-gray-500 max-w-2xl">
          Historial de cada carga de datos que subiste: de qué archivo viene, quién la subió y cuándo.
          Aquí revisas, editas, reviertes o eliminas cargas. Para gestionar tus SKUs y costos usa
          <span className="font-medium"> Productos</span>; para stock y reórdenes usa
          <span className="font-medium"> Inventario</span>.
        </p>
      </header>

      {/* Selectores de contexto */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-wrap items-end gap-4">
        <div>
          <label className="text-xs font-medium text-gray-500">Negocio</label>
          <select
            className="mt-1 block w-56 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
            value={businessId ?? ""}
            onChange={(e) => { setBusinessId(Number(e.target.value) || null); setStoreNbr(null); setExpanded(null); }}
          >
            <option value="">Selecciona un negocio</option>
            {businesses.data?.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>

        {businessId != null && (
          <div>
            <label className="text-xs font-medium text-gray-500">Ubicación</label>
            <select
              className="mt-1 block w-56 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
              value={storeNbr ?? ""}
              onChange={(e) => setStoreNbr(e.target.value === "" ? null : Number(e.target.value))}
            >
              <option value="">Todas las ubicaciones</option>
              {stores.data?.map((s) => (
                <option key={s.store_nbr} value={s.store_nbr}>
                  Ubicación {s.store_nbr}{s.city ? ` - ${s.city}` : ""}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Resumen */}
      {businessId != null && loads.length > 0 && (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
          {summary.map(({ label, value, icon: Icon, bg, text }) => (
            <div key={label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${bg}`}>
                <Icon className={`w-5 h-5 ${text}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-400 font-medium">{label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabla de cargas */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {businessId == null ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Database className="w-10 h-10 mb-2 opacity-30" />
            <p className="text-sm">Elige un negocio para ver sus cargas.</p>
          </div>
        ) : ingests.isLoading ? (
          <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Cargando cargas...</span>
          </div>
        ) : loads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <FileSpreadsheet className="w-10 h-10 mb-2 opacity-30" />
            <p className="text-sm">Este negocio no tiene cargas aún.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["", "Fecha", "Archivo", "Subió", "Filas", "Rango", "Unidad", "Estado", ""].map((h, i) => (
                    <th key={i} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {loads.map((log) => (
                  <RowGroup
                    key={log.id}
                    log={log}
                    open={expanded === log.id}
                    onToggle={() => setExpanded(expanded === log.id ? null : log.id)}
                    onRevert={() => setConfirm({ type: "revert", log })}
                    onDelete={() => setConfirm({ type: "delete", log })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Confirmaciones de carga */}
      <ConfirmModal
        isOpen={confirm?.type === "revert"}
        title="Revertir carga"
        message={confirm?.type === "revert"
          ? `La carga "${confirm.log.filename}" dejará de contar en pronósticos e inventario, pero sus ${confirm.log.records_loaded} filas no se borran. Puedes eliminarla después si quieres.`
          : ""}
        confirmLabel="Revertir"
        confirmClassName="bg-amber-500 text-white hover:opacity-90"
        isLoading={revertMut.isPending}
        onConfirm={() => confirm?.type === "revert" && revertMut.mutate(confirm.log.id)}
        onClose={() => setConfirm(null)}
      />
      <ConfirmModal
        isOpen={confirm?.type === "delete"}
        title="Eliminar carga"
        message={confirm?.type === "delete"
          ? `Se eliminará la carga "${confirm.log.filename}" y sus ${confirm.log.records_loaded} filas de forma permanente. Esta acción no se puede deshacer.`
          : ""}
        confirmLabel="Eliminar"
        confirmClassName="bg-red-600 text-white hover:opacity-90"
        isLoading={deleteMut.isPending}
        onConfirm={() => confirm?.type === "delete" && deleteMut.mutate(confirm.log.id)}
        onClose={() => setConfirm(null)}
      />
    </div>
  );
}

function RowGroup({ log, open, onToggle, onRevert, onDelete }: {
  log: IngestLogItem;
  open: boolean;
  onToggle: () => void;
  onRevert: () => void;
  onDelete: () => void;
}) {
  const qc = useQueryClient();
  const [recordToDelete, setRecordToDelete] = useState<number | null>(null);
  const [stockyReply, setStockyReply] = useState<string | null>(null);

  const records = useQuery({
    queryKey: ["ingest-records", log.id],
    queryFn: () => getIngestRecords(log.id),
    enabled: open,
  });

  const editMut = useMutation({
    mutationFn: ({ id, sales }: { id: number; sales: number }) => updateRecord(id, { sales }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingest-records", log.id] }),
  });
  const delRecMut = useMutation({
    mutationFn: (id: number) => deleteRecord(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ingest-records", log.id] });
      qc.invalidateQueries({ queryKey: ["ingests"] });
      setRecordToDelete(null);
    },
  });

  const askMut = useMutation({
    mutationFn: () => chatIngest(
      [{ role: "user", content: "Resume esta carga y dime si tiene huecos o ventas raras." }],
      `Carga ${log.filename}: familias ${(log.families || []).join(", ")}, rango ${log.date_range_start} a ${log.date_range_end}, ${log.records_loaded} filas, unidad ${log.sales_unit}, estado ${log.status}.`,
    ),
    onSuccess: (res) => setStockyReply(res.reply),
  });

  const reverted = log.status !== "active";

  return (
    <>
      <tr className={`hover:bg-gray-50 transition-colors ${reverted ? "opacity-60" : ""}`}>
        <td className="px-4 py-3">
          <button onClick={onToggle} className="p-1 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </td>
        <td className="px-4 py-3 text-gray-500">{new Date(log.created_at).toLocaleDateString("es-CL")}</td>
        <td className="px-4 py-3 font-medium text-gray-800">{log.filename}</td>
        <td className="px-4 py-3 text-gray-500">{log.uploader_name ?? "-"}</td>
        <td className="px-4 py-3 text-gray-700">{log.records_loaded.toLocaleString("es-CL")}</td>
        <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">{log.date_range_start} → {log.date_range_end}</td>
        <td className="px-4 py-3 text-gray-500">{log.sales_unit === "CLP" ? "CLP" : "uds"}</td>
        <td className="px-4 py-3">
          <StatusBadge status={log.status === "active" ? "Activo" : "Inactivo"} />
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2 justify-end">
            {log.status === "active" && (
              <button onClick={onRevert} title="Revertir" className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors">
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
            <button onClick={onDelete} title="Eliminar" className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </td>
      </tr>

      {open && (
        <tr>
          <td colSpan={9} className="bg-gray-50/70 px-6 py-4">
            {records.isLoading ? (
              <div className="flex items-center gap-2 text-gray-400 py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Cargando registros...</span>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {["Fecha", "Familia", "Venta", "Promo", ""].map((h, i) => (
                        <th key={i} className="px-4 py-2 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {records.data?.map((r) => (
                      <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-2 text-gray-500">{r.date}</td>
                        <td className="px-4 py-2 text-gray-700">{r.family}</td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            defaultValue={r.sales}
                            className="w-28 px-2 py-1 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                            onBlur={(e) => {
                              const v = Number(e.target.value);
                              if (v !== r.sales) editMut.mutate({ id: r.id, sales: v });
                            }}
                          />
                        </td>
                        <td className="px-4 py-2 text-gray-500">{r.onpromotion}</td>
                        <td className="px-4 py-2 text-right">
                          <button
                            onClick={() => setRecordToDelete(r.id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Stocky */}
            <div className="mt-4">
              <button
                onClick={() => askMut.mutate()}
                disabled={askMut.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50"
              >
                {askMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                Preguntar a Stocky
              </button>
              {stockyReply && (
                <div className="mt-2 p-3 bg-white border border-indigo-100 rounded-lg text-sm text-gray-700 prose prose-sm max-w-none">
                  <ReactMarkdown>{stockyReply}</ReactMarkdown>
                </div>
              )}
            </div>

            <ConfirmModalRecord
              open={recordToDelete != null}
              loading={delRecMut.isPending}
              onConfirm={() => recordToDelete != null && delRecMut.mutate(recordToDelete)}
              onClose={() => setRecordToDelete(null)}
            />
          </td>
        </tr>
      )}
    </>
  );
}

function ConfirmModalRecord({ open, loading, onConfirm, onClose }: {
  open: boolean; loading: boolean; onConfirm: () => void; onClose: () => void;
}) {
  return (
    <ConfirmModal
      isOpen={open}
      title="Eliminar registro"
      message="Se eliminará esta fila de ventas de forma permanente. ¿Continuar?"
      confirmLabel="Eliminar"
      confirmClassName="bg-red-600 text-white hover:opacity-90"
      isLoading={loading}
      onConfirm={onConfirm}
      onClose={onClose}
    />
  );
}
