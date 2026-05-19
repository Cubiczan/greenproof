'use client';

import { useEffect, useState } from 'react';
import {
  fetchStats,
  fetchRecentVerifications,
  fetchScoreDistribution,
  fetchStandardDistribution,
} from '@/lib/api';
import type {
  StatCards,
  Verification,
  VerificationScoreDistribution,
  CreditStandardDistribution,
  RiskLevel,
} from '@/lib/types';
import {
  Leaf,
  FolderCheck,
  ShoppingBag,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const riskColor: Record<RiskLevel, string> = {
  Low: 'text-emerald-400 bg-emerald-400/10',
  Medium: 'text-amber-400 bg-amber-400/10',
  High: 'text-red-400 bg-red-400/10',
};

const statusColor: Record<string, string> = {
  Verified: 'text-emerald-400 bg-emerald-400/10',
  Pending: 'text-amber-400 bg-amber-400/10',
  Failed: 'text-red-400 bg-red-400/10',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
}

const statCards = [
  { key: 'totalCreditsVerified' as const, label: 'Total Credits Verified', unit: 'tonnes CO₂', icon: Leaf },
  { key: 'projectsVerified' as const, label: 'Projects Verified', unit: '', icon: FolderCheck },
  { key: 'activeListings' as const, label: 'Active Listings', unit: '', icon: ShoppingBag },
  { key: 'avgScore' as const, label: 'Avg Verification Score', unit: '/ 100', icon: TrendingUp },
];

export default function OverviewPage() {
  const [stats, setStats] = useState<StatCards | null>(null);
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [scoreDist, setScoreDist] = useState<VerificationScoreDistribution[]>([]);
  const [standardDist, setStandardDist] = useState<CreditStandardDistribution[]>([]);

  useEffect(() => {
    fetchStats().then(setStats);
    fetchRecentVerifications().then(setVerifications);
    fetchScoreDistribution().then(setScoreDist);
    fetchStandardDistribution().then(setStandardDist);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white">Overview</h1>
        <p className="text-gray-400 text-sm mt-1">
          Real-time carbon credit verification metrics
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ key, label, unit, icon: Icon }) => {
          const value = stats?.[key];
          return (
            <div
              key={key}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-400">{label}</span>
                <div className="p-2 rounded-lg bg-emerald-500/10">
                  <Icon className="w-4 h-4 text-emerald-400" />
                </div>
              </div>
              {value !== undefined ? (
                <p className="text-2xl font-bold text-white">
                  {key === 'avgScore' ? value.toFixed(1) : formatNumber(value)}
                  <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
                </p>
              ) : (
                <div className="h-8 w-32 animate-pulse rounded bg-gray-800" />
              )}
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Score Distribution */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-4">
            Verification Score Distribution
          </h2>
          {scoreDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={scoreDist} barSize={36}>
                <XAxis
                  dataKey="range"
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  axisLine={{ stroke: '#374151' }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#f3f4f6',
                    fontSize: '13px',
                  }}
                  cursor={{ fill: 'rgba(16,185,129,0.06)' }}
                />
                <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 animate-pulse rounded bg-gray-800" />
          )}
        </div>

        {/* Credit Standards */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-4">
            Credit Standards
          </h2>
          {standardDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={standardDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {standardDist.map((entry, i) => (
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
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }}
                  formatter={(value) => (
                    <span style={{ color: '#9ca3af' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 animate-pulse rounded bg-gray-800" />
          )}
        </div>
      </div>

      {/* Recent Verifications Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h2 className="text-base font-semibold text-white">Recent Verifications</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-left">
                <th className="px-5 py-3 font-medium">Project</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium hidden sm:table-cell">Country</th>
                <th className="px-5 py-3 font-medium">Score</th>
                <th className="px-5 py-3 font-medium">Risk</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {verifications.length > 0 ? (
                verifications.map((v) => (
                  <tr
                    key={v.id}
                    className="border-b border-gray-800/60 hover:bg-gray-800/30 transition-colors"
                  >
                    <td className="px-5 py-3 font-medium text-white">{v.projectName}</td>
                    <td className="px-5 py-3 text-gray-400">{v.projectType}</td>
                    <td className="px-5 py-3 text-gray-400 hidden sm:table-cell">{v.country}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`font-semibold ${
                          v.score >= 80
                            ? 'text-emerald-400'
                            : v.score >= 60
                            ? 'text-amber-400'
                            : 'text-red-400'
                        }`}
                      >
                        {v.score}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          riskColor[v.riskLevel]
                        }`}
                      >
                        {v.riskLevel}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          statusColor[v.status]
                        }`}
                      >
                        {v.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-800/60">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-5 py-3">
                        <div className="h-4 w-24 animate-pulse rounded bg-gray-800" />
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
