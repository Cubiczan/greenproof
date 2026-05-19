'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, BarChart3, ShieldCheck, Coins, Store } from 'lucide-react';

const navItems = [
  { href: '/', label: 'Overview', icon: BarChart3 },
  { href: '/verify', label: 'Verify', icon: ShieldCheck },
  { href: '/credits', label: 'Credits', icon: Coins },
  { href: '/marketplace', label: 'Marketplace', icon: Store },
];

export default function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <div className="md:hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-950 border-b border-gray-800 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <span className="text-xl">🌿</span>
          <span className="text-base font-bold text-emerald-400 tracking-tight">
            GreenVerify AI
          </span>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="text-gray-400 hover:text-gray-200"
        >
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Dropdown */}
      {open && (
        <nav className="px-3 py-2 bg-gray-950 border-b border-gray-800 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === '/' ? pathname === '/' : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
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
          <div className="pt-2 pb-1 border-t border-gray-800 mt-2">
            <p className="text-[11px] text-gray-500 text-center">
              Powered by Portaldot
            </p>
            <div className="flex items-center justify-center gap-2 mt-1">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                POT
              </span>
              <span className="text-[11px] text-gray-500">Token</span>
            </div>
          </div>
        </nav>
      )}
    </div>
  );
}
