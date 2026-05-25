// frontend/src/pages/Datos.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, ChevronDown, ChevronRight, RotateCcw, Trash2, Loader2 } from "lucide-react";
import {
  listBusinesses, listBusinessStores, listIngests, getIngestRecords,
  revertIngest, deleteIngest, updateRecord, deleteRecord,
} from "../api/data";

export default function Datos() {
  const qc = useQueryClient();
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [storeNbr, setStoreNbr] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingests"] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteIngest(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingests"] }),
  });

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center gap-2">
        <Database className="w-6 h-6 text-indigo-600" />
        <h1 className="text-2xl font-bold">Datos</h1>
      </header>

      {/* Selector de negocio */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          className="border rounded-lg px-3 py-2"
          value={businessId ?? ""}
          onChange={(e) => { setBusinessId(Number(e.target.value) || null); setStoreNbr(null); }}
        >
          <option value="">Selecciona un negocio</option>
          {businesses.data?.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>

        {businessId != null && (
          <select
            className="border rounded-lg px-3 py-2"
            value={storeNbr ?? ""}
            onChange={(e) => setStoreNbr(e.target.value === "" ? null : Number(e.target.value))}
          >
            <option value="">Todas las ubicaciones</option>
            {stores.data?.map((s) => (
              <option key={s.store_nbr} value={s.store_nbr}>
                Ubicacion {s.store_nbr}{s.city ? ` - ${s.city}` : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Tabla de cargas */}
      {businessId == null ? (
        <p className="text-gray-500">Elige un negocio para ver sus cargas.</p>
      ) : ingests.isLoading ? (
        <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
      ) : ingests.data?.length === 0 ? (
        <p className="text-gray-500">Este negocio no tiene cargas aun.</p>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2 w-8"></th>
                <th className="px-3 py-2">Fecha</th>
                <th className="px-3 py-2">Archivo</th>
                <th className="px-3 py-2">Quien</th>
                <th className="px-3 py-2">Filas</th>
                <th className="px-3 py-2">Rango</th>
                <th className="px-3 py-2">Unidad</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ingests.data?.map((log) => (
                <RowGroup
                  key={log.id}
                  log={log}
                  open={expanded === log.id}
                  onToggle={() => setExpanded(expanded === log.id ? null : log.id)}
                  onRevert={() => revertMut.mutate(log.id)}
                  onDelete={() => {
                    if (confirm(`Eliminar la carga "${log.filename}" y sus ${log.records_loaded} filas?`))
                      deleteMut.mutate(log.id);
                  }}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RowGroup({ log, open, onToggle, onRevert, onDelete }: {
  log: import("../api/data").IngestLogItem;
  open: boolean;
  onToggle: () => void;
  onRevert: () => void;
  onDelete: () => void;
}) {
  const qc = useQueryClient();
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingest-records", log.id] }),
  });

  return (
    <>
      <tr className="border-t hover:bg-gray-50">
        <td className="px-3 py-2">
          <button onClick={onToggle}>
            {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </td>
        <td className="px-3 py-2">{new Date(log.created_at).toLocaleDateString("es-CL")}</td>
        <td className="px-3 py-2">{log.filename}</td>
        <td className="px-3 py-2">{log.uploader_name ?? "-"}</td>
        <td className="px-3 py-2">{log.records_loaded}</td>
        <td className="px-3 py-2">{log.date_range_start} -&gt; {log.date_range_end}</td>
        <td className="px-3 py-2">{log.sales_unit}</td>
        <td className="px-3 py-2">
          <span className={log.status === "active" ? "text-green-600" : "text-gray-400"}>
            {log.status === "active" ? "activa" : "revertida"}
          </span>
        </td>
        <td className="px-3 py-2 flex gap-2">
          {log.status === "active" && (
            <button onClick={onRevert} title="Revertir" className="text-amber-600">
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          <button onClick={onDelete} title="Eliminar" className="text-red-600">
            <Trash2 className="w-4 h-4" />
          </button>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={9} className="bg-gray-50 px-6 py-3">
            {records.isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <table className="w-full text-xs">
                <thead className="text-left text-gray-500">
                  <tr><th className="py-1">Fecha</th><th>Familia</th><th>Venta</th><th>Promo</th><th></th></tr>
                </thead>
                <tbody>
                  {records.data?.map((r) => (
                    <tr key={r.id} className="border-t">
                      <td className="py-1">{r.date}</td>
                      <td>{r.family}</td>
                      <td>
                        <input
                          type="number"
                          defaultValue={r.sales}
                          className="w-24 border rounded px-1"
                          onBlur={(e) => {
                            const v = Number(e.target.value);
                            if (v !== r.sales) editMut.mutate({ id: r.id, sales: v });
                          }}
                        />
                      </td>
                      <td>{r.onpromotion}</td>
                      <td>
                        <button className="text-red-500" onClick={() => {
                          if (confirm("Eliminar este registro?")) delRecMut.mutate(r.id);
                        }}>
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
