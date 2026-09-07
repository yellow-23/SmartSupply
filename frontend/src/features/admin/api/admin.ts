import api from "../../../shared/api/axios.instance";

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: "platform_admin" | "business_admin" | "analyst";
  is_active: boolean;
  business_id: number | null;
  business_name: string;
}

export interface AdminBusiness {
  id: number;
  name: string;
  type: string | null;
  onboarding_completed: boolean;
  user_count: number;
  sales_rows: number;
}

export async function listAdminUsers(): Promise<AdminUser[]> {
  const { data } = await api.get("/admin/users");
  return data;
}

export async function updateAdminUser(id: number, body: { is_active?: boolean; role?: string }): Promise<AdminUser> {
  const { data } = await api.patch(`/admin/users/${id}`, body);
  return data;
}

export async function listAdminBusinesses(): Promise<AdminBusiness[]> {
  const { data } = await api.get("/admin/businesses");
  return data;
}

export async function deleteAdminUser(id: number): Promise<void> {
  await api.delete(`/admin/users/${id}`);
}

export async function deleteAdminBusiness(id: number): Promise<void> {
  await api.delete(`/admin/businesses/${id}`);
}
