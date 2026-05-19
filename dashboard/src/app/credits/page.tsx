'use client';

import { useEffect, useState, useMemo } from 'react';
import { fetchCreditNFTs } from '@/lib/api';
import type { CreditNFT, ProjectType, CreditStandard } from '@/lib/types';
import { getCountryFlag } from '@/lib/data';
import { Coins, Filter, ExternalLink } from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const standardBadge: Record<CreditStandard, string> = {
  VCS: 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  'Gold Standard': 'bg-amber-400/10 text-amber-400 border-amber-400/20',
  CDM: 'bg-violet-400/10 text-violet-400 border-violet-400/20',
};

export default function CreditsPage() {
  const [nfts, setNfts] = useState<CreditNFT[]>([]);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [standardFilter, setStandardFilter] = useState<string>('all');

  useEffect(() => {
    fetchCreditNFTs().then(setNfts);
  }, []);

  const filtered = useMemo(() => {
    return nfts.filter((n) => {
      if (typeFilter !== 'all' && n.projectType !== typeFilter) return false;
      if (standardFilter !== 'all' && n.creditStandard !== standardFilter) return false;
      return true;
    });
  }, [nfts, typeFilter, standardFilter]);

  const typeDist = useMemo(() => {
    const counts: Record<string, number> = {};
    nfts.forEach((n) => {
      counts[n.projectType] = (counts[n.projectType] || 0) + n.creditAmount;
    });
    const colors: Record<string, string> = {
      Reforestation: '#10b981',
      'Renewable Energy': '#f59e0b',
      'Methane Capture': '#6366f1',
      Industrial: '#ef4444',
    };
    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      color: colors[name] ?? '#6b7280',
    }));
  }, [nfts]);

  const projectTypes: ProjectType[] = ['Reforestation', 'Renewable Energy', 'Methane Capture', 'Industrial'];
  const standards: CreditStandard[] = ['VCS', 'Gold Standard', 'CDM'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
          <Coins className="w-7 h-7 text-emerald-400" />
          Credit NFTs
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Verified carbon credits minted as NFTs on Portaldot
        </p>
      </div>

      {/* Chart + Filters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Filters */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            Filters
          </h2>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Project Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="all">All Types</option>
              {projectTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Credit Standard
            </label>
            <select
              value={standardFilter}
              onChange={(e) => setStandardFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="all">All Standards</option>
              {standards.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <p className="text-xs text-gray-500">
            Showing {filtered.length} of {nfts.length} credits
          </p>
        </div>

        {/* Distribution Chart */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-4">
            Credit Type Distribution
          </h2>
          {typeDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={typeDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {typeDist.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#f3f4f6',
                    fontSize: '13px',
                  }}
                  formatter={(value) => [`${Number(value).toLocaleString()} tCO₂`, 'Volume']}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px' }}
                  formatter={(value) => (
                    <span style={{ color: '#9ca3af' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 animate-pulse rounded bg-gray-800" />
          )}
        </div>
      </div>

      {/* NFT Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((nft) => (
          <div
            key={nft.tokenId}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {nft.tokenId}
              </span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                  standardBadge[nft.creditStandard]
                }`}
              >
                {nft.creditStandard}
              </span>
            </div>

            {/* Project Name */}
            <h3 className="text-sm font-semibold text-white mb-3 truncate">
              {nft.projectName}
            </h3>

            {/* Details */}
            <div className="space-y-2 text-sm flex-1">
              <div className="flex justify-between">
                <span className="text-gray-400">Credits</span>
                <span className="text-white font-medium">
                  {nft.creditAmount.toLocaleString()} tCO₂
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Vintage</span>
                <span className="text-white">{nft.vintageYear}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Country</span>
                <span className="text-white">
                  {getCountryFlag(nft.country)} {nft.country}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Owner</span>
                <span className="text-gray-300 font-mono text-xs">
                  {nft.ownerAddress}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Minted</span>
                <span className="text-gray-300">{nft.mintedDate}</span>
              </div>
            </div>

            {/* TX Hash */}
            <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between">
              <span className="text-xs text-gray-500 font-mono truncate">
                TX: {nft.txHash}
              </span>
              <ExternalLink className="w-3.5 h-3.5 text-gray-500 shrink-0 ml-2" />
            </div>
          </div>
        ))}

        {filtered.length === 0 && nfts.length > 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            No credits match the selected filters.
          </div>
        )}

        {nfts.length === 0 &&
          Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5"
            >
              <div className="h-4 w-20 animate-pulse rounded bg-gray-800 mb-3" />
              <div className="h-4 w-40 animate-pulse rounded bg-gray-800 mb-4" />
              {Array.from({ length: 5 }).map((_, j) => (
                <div key={j} className="flex justify-between py-1.5">
                  <div className="h-3 w-16 animate-pulse rounded bg-gray-800" />
                  <div className="h-3 w-20 animate-pulse rounded bg-gray-800" />
                </div>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}
