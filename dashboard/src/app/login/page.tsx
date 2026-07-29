"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth";
import { useUserStore } from "@/stores/userStore";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useUserStore((s) => s.setSession);
  const [email, setEmail] = useState("alex@verilumen.ai");
  const [password, setPassword] = useState("changeme123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await authApi.login(email, password);
      const user = await authApi.getMe();
      setSession(user, tokens.access_token);
      router.replace("/dashboard");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#090B12] px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-6 rounded-2xl border border-[#2D3748] bg-[#111827] p-8 shadow-xl"
      >
        <div>
          <h1 className="text-2xl font-semibold text-white">VERILUMEN</h1>
          <p className="mt-1 text-sm text-slate-400">Sign in to the test intelligence platform</p>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border-[#2D3748] bg-[#090B12]"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border-[#2D3748] bg-[#090B12]"
              required
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>
        <Button type="submit" className="w-full bg-[#7C3AED] hover:bg-[#6D28D9]" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
        <p className="text-center text-xs text-slate-500">
          Demo: alex@verilumen.ai / changeme123 (after backend seed)
        </p>
      </form>
    </div>
  );
}
