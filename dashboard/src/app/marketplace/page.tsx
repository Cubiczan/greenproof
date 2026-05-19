'use client';

import { useEffect, useState } from 'react';
import {
  fetchListings,
  fetchMarketplaceStats,
} from '@/lib/api';
import type { MarketplaceListing, MarketplaceStats } from '@/lib/types';
import {
  Store,
  TrendingUp,
  BarChart3,
  DollarSign,
  ShoppingCart,
  ArrowUpDown,
} from 'lucide-react';

const standardBadge: Record<string, string> = {
  VCS: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  'Gold Standard': 'bg-amber-400/10 text-amber-400 border-amber-400/20',
  CDM: 'bg-violet-400/10 text-violet-400 border-violet-400/20',
};

function formatPOT(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
}

const statsMeta = [
  { key: 'totalVolumeTraded' as const, label: 'Total Volume Traded', icon: TrendingUp, unit: ' POT' },
  { key: 'numberOfTrades' as const, label: 'Number of Trades', icon: BarChart3, unit: '' },
  { key: 'floorPrice' as const, label: 'Floor Price', icon: DollarSign, unit: ' POT' },
  { key: 'avgPrice' as const, label: 'Avg Price', icon: ArrowUpDown, unit: ' POT' },
];

export default function MarketplacePage() {
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [buying, setBuying] = useState<string | null>(null);

  useEffect(() => {
    fetchListings().then(setListings);
    fetchMarketplaceStats().then(setStats);
  }, []);

  const handleBuy = (tokenId: string) => {
    setBuying(tokenId);
    setTimeout(() => {
      setBuying(null);
      alert(`Purchase of ${tokenId} initiated! (Demo — blockchain tx would be sent here)`);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
          <Store className="w-7 h-7 text-emerald-400" />
          Marketplace
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Buy and sell verified carbon credit NFTs on Portaldot
        </p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsMeta.map(({ key, label, icon: Icon, unit }) => {
          const value = stats?.[key];
          return (
            <div
              key={key}
              className="bg-gray-900 border border-gray-800 rounded-xl p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <Icon className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-400">{label}</span>
              </div>
              {value !== undefined ? (
                <p className="text-lg font-bold text-white">
                  {key === 'floorPrice' || key === 'avgPrice'
                    ? value.toFixed(2)
                    : formatPOT(value)}
                  <span className="text-xs font-normal text-gray-500 ml-0.5">
                    {unit}
                  </span>
                </p>
              ) : (
                <div className="h-6 w-24 animate-pulse rounded bg-gray-800" />
              )}
            </div>
          );
        })}
      </div>

      {/* Listings Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {listings.map((listing) => (
          <div
            key={listing.tokenId}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {listing.tokenId}
              </span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                  standardBadge[listing.creditStandard] ?? 'bg-gray-700 text-gray-300 border-gray-600'
                }`}
              >
                {listing.creditStandard}
              </span>
            </div>

            {/* Project Name */}
            <h3 className="text-sm font-semibold text-white mb-1 truncate">
              {listing.projectName}
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              {listing.projectType} &middot; Vintage {listing.vintageYear}
            </p>

            {/* Price (Big Green Number) */}
            <div className="mb-4 p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10 text-center">
              <p className="text-xs text-gray-400 mb-1">Price</p>
              <p className="text-3xl font-bold text-emerald-400">
                {listing.pricePOT.toLocaleString()}
                <span className="text-sm font-medium ml-1">POT</span>
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {(
                  listing.pricePOT / listing.creditAmount
                ).toFixed(4)}{' '}
                POT / tCO₂
              </p>
            </div>

            {/* Details */}
            <div className="space-y-1.5 text-sm flex-1 mb-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Credits</span>
                <span className="text-white font-medium">
                  {listing.creditAmount.toLocaleString()} tCO₂
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Seller</span>
                <span className="text-gray-300 font-mono text-xs">
                  {listing.sellerAddress}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Listed</span>
                <span className="text-gray-300">{listing.listedDate}</span>
              </div>
            </div>

            {/* Buy Button */}
            <button
              onClick={() => handleBuy(listing.tokenId)}
              disabled={buying !== null}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {buying === listing.tokenId ? (
                <>
                  <ShoppingCart className="w-4 h-4 animate-pulse" />
                  Processing...
                </>
              ) : (
                <>
                  <ShoppingCart className="w-4 h-4" />
                  Buy
                </>
              )}
            </button>
          </div>
        ))}

        {listings.length === 0 &&
          Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5"
            >
              <div className="h-4 w-20 animate-pulse rounded bg-gray-800 mb-3" />
              <div className="h-4 w-40 animate-pulse rounded bg-gray-800 mb-1" />
              <div className="h-3 w-28 animate-pulse rounded bg-gray-800 mb-4" />
              <div className="h-16 animate-pulse rounded-lg bg-gray-800 mb-4" />
              {Array.from({ length: 3 }).map((_, j) => (
                <div key={j} className="flex justify-between py-1.5">
                  <div className="h-3 w-16 animate-pulse rounded bg-gray-800" />
                  <div className="h-3 w-20 animate-pulse rounded bg-gray-800" />
                </div>
              ))}
              <div className="h-10 animate-pulse rounded-lg bg-gray-800 mt-4" />
            </div>
          ))}
      </div>
    </div>
  );
}
