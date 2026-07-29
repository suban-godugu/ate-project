import { redirect } from "next/navigation";

/** Wafer Analysis UI removed — keep route so old links redirect cleanly. */
export default function WaferAnalysisPage() {
  redirect("/dashboard");
}
