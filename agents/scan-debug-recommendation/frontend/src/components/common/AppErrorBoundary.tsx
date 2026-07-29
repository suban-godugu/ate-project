"use client";

import { Component, type ReactNode } from "react";

export class AppErrorBoundary extends Component<
  { children: ReactNode; title?: string },
  { hasError: boolean; message?: string }
> {
  state = { hasError: false, message: undefined as string | undefined };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card gradient-border mx-auto max-w-2xl p-6 text-center">
          <div className="text-[10px] uppercase tracking-[0.16em] text-warning">Recoverable error</div>
          <h2 className="mt-2 font-display text-xl font-semibold text-white">
            {this.props.title ?? "Something went wrong"}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            The dashboard hit a client error. Hard refresh the page. If the live API is not running,
            start it and reload.
          </p>
          {this.state.message ? (
            <p className="mt-3 rounded-lg bg-black/30 px-3 py-2 font-mono text-xs text-slate-500">
              {this.state.message}
            </p>
          ) : null}
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
          >
            Reload page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
