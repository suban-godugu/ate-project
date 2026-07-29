"use client";

import { Component, type ReactNode } from "react";

export class ChartErrorBoundary extends Component<
  { children: ReactNode; title?: string },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card gradient-border p-4 text-sm text-muted">
          {this.props.title ?? "Charts"} could not be rendered in this browser session.
        </div>
      );
    }
    return this.props.children;
  }
}
