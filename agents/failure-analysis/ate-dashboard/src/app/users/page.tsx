"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { notify } from "@/stores/toastStore";

type UserRow = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  last_login_at?: string | null;
};

export default function UsersPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "viewer",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const { data } = await api.get("/users");
      return data as { users: UserRow[]; roles: string[] };
    },
  });

  const create = useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/users", form);
      return data;
    },
    onSuccess: () => {
      notify({ title: "User Created", variant: "success" });
      setForm({ email: "", full_name: "", password: "", role: "viewer" });
      void qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: () => notify({ title: "Create Failed", variant: "error" }),
  });

  async function disableUser(id: string) {
    await api.post(`/users/${id}/disable`);
    notify({ title: "User Disabled", variant: "warning" });
    void qc.invalidateQueries({ queryKey: ["users"] });
  }

  async function deleteUser(id: string) {
    if (!confirm("Delete this user permanently?")) return;
    await api.delete(`/users/${id}`);
    notify({ title: "User Deleted", variant: "success" });
    void qc.invalidateQueries({ queryKey: ["users"] });
  }

  async function resetPassword(id: string) {
    const password = prompt("Enter new password (min 8 characters)");
    if (!password || password.length < 8) return;
    await api.post(`/users/${id}/reset-password`, { password });
    notify({ title: "Password Reset", variant: "success" });
  }

  function onCreate(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">User Management</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Create, edit, disable, and reset passwords for dashboard users.
        </p>
      </header>

      <form
        onSubmit={onCreate}
        className="glass-panel grid gap-3 rounded-2xl p-4 md:grid-cols-5"
        aria-label="Create user"
      >
        <input
          required
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
        />
        <input
          required
          placeholder="Full name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
        />
        <input
          required
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
        />
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
          aria-label="Role"
        >
          {(data?.roles || ["administrator", "engineer", "operator", "viewer"]).map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={create.isPending}
          className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
        >
          Create User
        </button>
      </form>

      <div className="glass-panel overflow-hidden rounded-2xl" data-testid="users-table">
        <table className="w-full text-sm">
          <thead className="text-xs uppercase text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Role</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Last Login</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-[var(--muted)]">
                  Loading users…
                </td>
              </tr>
            )}
            {(data?.users || []).map((u) => (
              <tr key={u.id} className="border-t border-white/5">
                <td className="px-4 py-3">
                  <div className="font-medium">{u.full_name || "—"}</div>
                  <div className="text-xs text-[var(--muted)]">{u.email}</div>
                </td>
                <td className="px-4 py-3 capitalize">{u.role}</td>
                <td className="px-4 py-3 capitalize">{u.status}</td>
                <td className="px-4 py-3 text-xs">
                  {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "—"}
                </td>
                <td className="space-x-2 px-4 py-3 text-right text-xs">
                  <button type="button" onClick={() => resetPassword(u.id)} className="hover:underline">
                    Reset Password
                  </button>
                  <button type="button" onClick={() => disableUser(u.id)} className="hover:underline">
                    Disable
                  </button>
                  <button type="button" onClick={() => deleteUser(u.id)} className="text-[var(--danger)] hover:underline">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
