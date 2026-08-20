"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { logout } = useAuth();

  const links = [
    { href: "/dashboard", label: "Overview" },
    { href: "/dashboard/documents", label: "Documents" },
    { href: "/chat", label: "Chat" },
  ];

  return (
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <aside className="w-64 border-r bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 flex flex-col">
        <div className="h-14 flex items-center px-6 border-b border-zinc-200 dark:border-zinc-800">
          <h1 className="font-semibold text-lg">Enterprise RAG</h1>
        </div>
        <nav className="flex-1 py-4 px-3 space-y-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center px-3 py-2 text-sm rounded-md transition-colors ${
                pathname === link.href
                  ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50 font-medium"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-50"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
          <Button variant="outline" className="w-full justify-start" onClick={logout}>
            Logout
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center px-8 bg-white dark:bg-zinc-900">
          {/* Header area */}
        </div>
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
