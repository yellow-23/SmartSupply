import { useState } from "react";
import { Shield, Building2, Loader2, Trash2 } from "lucide-react";
import { motion } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listAdminUsers, listAdminBusinesses, updateAdminUser, deleteAdminUser, deleteAdminBusiness,
  AdminUser, AdminBusiness,
} from "../api/admin";
import { useAuthStore } from "../../auth/store/authStore";
import Modal from "../../../shared/ui/Modal";
import { toast } from "../../../shared/ui/toastStore";

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.015, duration: 0.12 } }),
};

const ROLE_LABEL: Record<string, string> = {
  platform_admin: "Admin plataforma",
  business_admin: "Admin negocio",
  analyst: "Analista",
};

export default function Admin() {
  const qc = useQueryClient();
  const currentUserId = useAuthStore((s) => s.user?.id);
  const [tab, setTab] = useState<"users" | "businesses">("users");
  const [deleteUserTarget, setDeleteUserTarget] = useState<AdminUser | null>(null);
  const [deleteBizTarget, setDeleteBizTarget] = useState<AdminBusiness | null>(null);

  const { data: users, isLoading: loadingUsers } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: listAdminUsers,
    enabled: tab === "users",
  });

  const { data: businesses, isLoading: loadingBiz } = useQuery({
    queryKey: ["admin", "businesses"],
    queryFn: listAdminBusinesses,
    enabled: tab === "businesses",
  });

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: { is_active?: boolean; role?: string } }) => updateAdminUser(id, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin", "users"] }); toast.success("Usuario actualizado"); },
  });

  const deleteUserMut = useMutation({
    mutationFn: deleteAdminUser,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin", "users"] }); setDeleteUserTarget(null); toast.success("Usuario eliminado"); },
  });

  const deleteBizMut = useMutation({
    mutationFn: deleteAdminBusiness,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "businesses"] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      setDeleteBizTarget(null);
      toast.success("Negocio eliminado");
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        {[
          { key: "users" as const, label: "Usuarios", icon: Shield },
          { key: "businesses" as const, label: "Negocios", icon: Building2 },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg font-medium transition-colors ${
              tab === key ? "bg-orange-600 text-white" : "bg-white text-gray-500 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === "users" && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm">Cargando usuarios...</span>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {["Nombre", "Email", "Negocio", "Rol", "Activo", ""].map((h) => (
                      <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(users ?? []).map((u: AdminUser, i) => (
                    <motion.tr
                      key={u.id}
                      custom={i}
                      initial="hidden"
                      animate="visible"
                      variants={rowVariants}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-gray-800">{u.name}</td>
                      <td className="px-6 py-4 text-gray-500">{u.email}</td>
                      <td className="px-6 py-4 text-gray-500">{u.business_name || <span className="text-gray-300 italic">Sin negocio</span>}</td>
                      <td className="px-6 py-4">
                        <select
                          value={u.role}
                          onChange={(e) => updateMut.mutate({ id: u.id, body: { role: e.target.value } })}
                          className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                        >
                          {Object.entries(ROLE_LABEL).map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => updateMut.mutate({ id: u.id, body: { is_active: !u.is_active } })}
                          className={`text-xs px-2 py-1 rounded-full font-medium ${
                            u.is_active ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"
                          }`}
                        >
                          {u.is_active ? "Activo" : "Inactivo"}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setDeleteUserTarget(u)}
                          disabled={u.id === currentUserId}
                          title={u.id === currentUserId ? "No puedes eliminar tu propia cuenta" : undefined}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-400 disabled:cursor-not-allowed"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {tab === "businesses" && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            {loadingBiz ? (
              <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm">Cargando negocios...</span>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {["Negocio", "Tipo", "Usuarios", "Filas de ventas", "Onboarding", ""].map((h) => (
                      <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(businesses ?? []).map((b, i) => (
                    <motion.tr
                      key={b.id}
                      custom={i}
                      initial="hidden"
                      animate="visible"
                      variants={rowVariants}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-gray-800">{b.name}</td>
                      <td className="px-6 py-4 text-gray-500">{b.type ?? "—"}</td>
                      <td className="px-6 py-4 text-gray-500">{b.user_count}</td>
                      <td className="px-6 py-4 text-gray-500">{b.sales_rows.toLocaleString("es-CL")}</td>
                      <td className="px-6 py-4">
                        {b.onboarding_completed ? (
                          <span className="text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-600 font-medium">Completo</span>
                        ) : (
                          <span className="text-xs px-2 py-1 rounded-full bg-amber-50 text-amber-600 font-medium">Pendiente</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setDeleteBizTarget(b)}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      <Modal open={!!deleteUserTarget} onClose={() => setDeleteUserTarget(null)} className="max-w-sm">
          <div className="p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-1">Eliminar usuario</h2>
            <p className="text-sm text-gray-500 mb-5">
              ¿Seguro que quieres eliminar a <span className="font-medium text-gray-800">{deleteUserTarget?.name}</span> ({deleteUserTarget?.email})?
              Esta acción no se puede deshacer.
            </p>
            {deleteUserMut.error && (
              <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">
                {(deleteUserMut.error as any).response?.data?.detail ?? "Error al eliminar"}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setDeleteUserTarget(null)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors active:scale-[0.97]">
                Cancelar
              </button>
              <button
                onClick={() => deleteUserTarget && deleteUserMut.mutate(deleteUserTarget.id)}
                disabled={deleteUserMut.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 transition-transform active:scale-[0.97]"
              >
                {deleteUserMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Eliminar
              </button>
            </div>
          </div>
      </Modal>

      <Modal open={!!deleteBizTarget} onClose={() => setDeleteBizTarget(null)} className="max-w-sm">
          <div className="p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-1">Eliminar negocio</h2>
            <p className="text-sm text-gray-500 mb-5">
              ¿Seguro que quieres eliminar <span className="font-medium text-gray-800">{deleteBizTarget?.name}</span>?
              Se borran sus {deleteBizTarget?.sales_rows.toLocaleString("es-CL")} filas de ventas y datos asociados. Sus {deleteBizTarget?.user_count} usuario{deleteBizTarget?.user_count !== 1 ? "s" : ""} no se elimina{deleteBizTarget?.user_count !== 1 ? "n" : ""}, quedan sin negocio. Esta acción no se puede deshacer.
            </p>
            {deleteBizMut.error && (
              <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg mb-3">
                {(deleteBizMut.error as any).response?.data?.detail ?? "Error al eliminar"}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setDeleteBizTarget(null)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors active:scale-[0.97]">
                Cancelar
              </button>
              <button
                onClick={() => deleteBizTarget && deleteBizMut.mutate(deleteBizTarget.id)}
                disabled={deleteBizMut.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 transition-transform active:scale-[0.97]"
              >
                {deleteBizMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Eliminar
              </button>
            </div>
          </div>
      </Modal>
    </div>
  );
}
