'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  ShieldCheck,
  Coins,
  Store,
} from 'lucide-react';

const navItems = [
  { href: '/', label: 'Overview', icon: BarChart3 },
  { href: '/verify', label: 'Verify', icon: ShieldCheck },
  { href: '/credits', label: 'Credits', icon: Coins },
  { href: '/marketplace', label: 'Marketplace', icon: Store },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex flex-col w-64 min-h-screen bg-gray-950 border-r border-gray-800">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-800">
        <span className="text-2xl">🌿</span>
        <span className="text-lg font-bold text-emerald-400 tracking-tight">
          GreenVerify AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                }
              `}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-800 space-y-2">
        <p className="text-[11px] text-gray-500 text-center">
          Powered by Portaldot
        </p>
        <div className="flex items-center justify-center gap-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            POT
          </span>
          <span className="text-[11px] text-gray-500">Token</span>
        </div>
      </div>
    </aside>
  );
}
