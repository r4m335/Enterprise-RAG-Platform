import { redirect } from "next/navigation";

export default function DashboardPage() {
  // Redirect to documents as the main dashboard page
  redirect("/dashboard/documents");
}
