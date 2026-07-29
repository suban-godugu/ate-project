"use client";

import { FormEvent, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { loginRequest } from "@/services/auth";
import { useAuthStore } from "@/stores/authStore";
import { notify } from "@/stores/toastStore";
import { logger } from "@/lib/logger";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("admin@verilumen.local");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await loginRequest(email, password);
      setSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: data.user,
      });
      logger.info("login_success", { email: data.user.email, role: data.user.role });
      notify({ title: "Signed in", description: `Welcome, ${data.user.full_name || data.user.email}`, variant: "success" });
      const next = params.get("next") || "/overview";
      router.replace(next);
    } catch (err) {
      const message =
        err && typeof err === "object" && "response" in err
          ? "Invalid email or password"
          : "Unable to reach authentication service";
      setError(message);
      logger.error("login_failed", { email });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <form
        onSubmit={onSubmit}
        className="glass-panel w-full max-w-md space-y-5 rounded-2xl p-8"
        aria-label="Sign in"
      >
        <div>
          <p className="text-xs font-semibold tracking-[0.2em] text-[var(--accent)]">
            VERILUMEN
          </p>
          <h1 className="mt-1 text-2xl font-semibold">Sign in</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Semiconductor Failure Analysis Workbench
          </p>
        </div>

        <label className="block text-sm">
          <span className="text-[var(--muted)]">Email</span>
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            aria-required="true"
          />
        </label>

        <label className="block text-sm">
          <span className="text-[var(--muted)]">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:ring-2 focus:ring-[var(--accent)]"
            aria-required="true"
          />
        </label>

        {error && (
          <p role="alert" className="text-sm text-[var(--danger)]">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <p className="text-xs text-[var(--muted)]">
          Default admin is created on first boot when the user table is empty.
        </p>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-[var(--muted)]">Loading…</div>}>
      <LoginForm />
    </Suspense>
  );
}
