"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  Database,
  FlaskConical,
  GitCompareArrows,
  History,
  LayoutDashboard,
  ShieldCheck,
} from "lucide-react";

const NAVIGATION = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/run", label: "Run Experiment", icon: FlaskConical },
  { href: "/dataset", label: "Test Dataset", icon: Database },
  { href: "/comparison", label: "Strategy Comparison", icon: GitCompareArrows },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/history", label: "Experiment History", icon: History },
  { href: "/docs", label: "Documentation", icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href) || (href === "/history" && pathname.startsWith("/experiment"));

  return (
    <aside className="bg-navy-900 text-slate-200 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col">
      <div className="flex items-center gap-3 px-5 py-4 lg:py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10">
          <ShieldCheck className="h-5 w-5 text-white" aria-hidden />
        </div>
        <div>
          <div className="text-base font-semibold tracking-tight text-white">ContextShield</div>
          <div className="text-[11px] leading-tight text-slate-400">Testing the boundaries of trust in LLMs.</div>
        </div>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:overflow-visible lg:pb-0" aria-label="Main">
        {NAVIGATION.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(href) ? "page" : undefined}
            className={`flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
              isActive(href) ? "bg-white/10 font-medium text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <Icon className="h-4 w-4" aria-hidden />
            {label}
          </Link>
        ))}
      </nav>
      <div className="hidden border-t border-white/10 px-5 py-4 text-[11px] leading-relaxed text-slate-400 lg:block">
        Prompt Engineering (SCSE4041)
        <br />
        Bennett University
      </div>
    </aside>
  );
}
