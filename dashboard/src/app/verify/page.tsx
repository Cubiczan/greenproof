'use client';

import { useState, useEffect } from 'react';
import { submitVerification, fetchRecentVerifications } from '@/lib/api';
import type {
  VerifyFormInput,
  VerifyResult,
  Verification,
  ProjectType,
  CreditStandard,
  RiskLevel,
} from '@/lib/types';
import { ShieldCheck, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

const projectTypes: ProjectType[] = ['Reforestation', 'Renewable Energy', 'Methane Capture', 'Industrial'];
const creditStandards: CreditStandard[] = ['VCS', 'Gold Standard', 'CDM'];

const riskColor: Record<RiskLevel, string> = {
  Low: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  Medium: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  High: 'text-red-400 bg-red-400/10 border-red-400/20',
};

const recentResults: Verification[] = [
  { id: 'r-1', projectName: 'Congo Basin Reforestation', projectType: 'Reforestation', country: 'DRC', score: 91, riskLevel: 'Low', status: 'Verified', date: '2025-01-14' },
  { id: 'r-2', projectName: 'Rajasthan Solar Grid', projectType: 'Renewable Energy', country: 'India', score: 76, riskLevel: 'Medium', status: 'Verified', date: '2025-01-11' },
  { id: 'r-3', projectName: 'Landfill Gas Capture Metro', projectType: 'Methane Capture', country: 'Colombia', score: 63, riskLevel: 'Medium', status: 'Pending', date: '2025-01-09' },
];

export default function VerifyPage() {
  const [form, setForm] = useState<VerifyFormInput>({
    projectName: '',
    description: '',
    projectType: 'Reforestation',
    country: '',
    vintageYear: 2024,
    estimatedAnnualCredits: 0,
    creditStandard: 'VCS',
    documentation: '',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [recent, setRecent] = useState<Verification[]>([]);

  useEffect(() => {
    fetchRecentVerifications()
      .then((data) => setRecent(data.length > 0 ? data.slice(0, 3) : recentResults));
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === 'vintageYear' || name === 'estimatedAnnualCredits'
          ? Number(value)
          : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await submitVerification(form);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor =
    result && result.score >= 80
      ? 'text-emerald-400'
      : result && result.score >= 60
      ? 'text-amber-400'
      : 'text-red-400';

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-7 h-7 text-emerald-400" />
          Verify Project
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Submit a carbon project for AI-powered verification
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-gray-900 border border-gray-800 rounded-xl p-5 md:p-6 space-y-5"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Project Name
            </label>
            <input
              name="projectName"
              value={form.projectName}
              onChange={handleChange}
              required
              placeholder="e.g. Amazon Reforestation Phase III"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Country */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Country
            </label>
            <input
              name="country"
              value={form.country}
              onChange={handleChange}
              required
              placeholder="e.g. Brazil"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Project Type */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Project Type
            </label>
            <select
              name="projectType"
              value={form.projectType}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              {projectTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Credit Standard */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Credit Standard
            </label>
            <select
              name="creditStandard"
              value={form.creditStandard}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              {creditStandards.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Vintage Year */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Vintage Year
            </label>
            <input
              name="vintageYear"
              type="number"
              min={2020}
              max={2026}
              value={form.vintageYear}
              onChange={handleChange}
              required
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* Estimated Annual Credits */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Estimated Annual Credits (tonnes CO₂)
            </label>
            <input
              name="estimatedAnnualCredits"
              type="number"
              min={0}
              value={form.estimatedAnnualCredits}
              onChange={handleChange}
              required
              placeholder="e.g. 50000"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Description
          </label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            required
            rows={3}
            placeholder="Brief description of the carbon reduction project..."
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
          />
        </div>

        {/* Documentation */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Documentation
          </label>
          <textarea
            name="documentation"
            value={form.documentation}
            onChange={handleChange}
            required
            rows={6}
            placeholder="Paste full project documentation, methodology, baseline study, and monitoring plan here..."
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-6 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4" />
              Submit for Verification
            </>
          )}
        </button>
      </form>

      {/* Result Card */}
      {result && (
        <div
          className={`border rounded-xl p-5 md:p-6 space-y-5 ${
            result.pass
              ? 'bg-gray-900 border-emerald-500/30'
              : 'bg-gray-900 border-red-500/30'
          }`}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Verification Result</h2>
            {result.pass ? (
              <span className="flex items-center gap-1.5 text-sm font-medium text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">
                <CheckCircle2 className="w-4 h-4" /> PASSED
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-sm font-medium text-red-400 bg-red-400/10 px-3 py-1 rounded-full">
                <XCircle className="w-4 h-4" /> FAILED
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Score */}
            <div className="text-center p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400 mb-1">Score</p>
              <p className={`text-4xl font-bold ${scoreColor}`}>{result.score}</p>
              <p className="text-xs text-gray-500 mt-1">out of 100</p>
            </div>

            {/* Risk Level */}
            <div className="text-center p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400 mb-1">Risk Level</p>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-semibold border ${
                  riskColor[result.riskLevel]
                }`}
              >
                {result.riskLevel}
              </span>
            </div>

            {/* Recommended Credits */}
            <div className="text-center p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400 mb-1">Recommended Credits</p>
              <p className="text-2xl font-bold text-white">
                {result.recommendedCreditAmount.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-1">tonnes CO₂ / year</p>
            </div>
          </div>

          {/* Assessment */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-2">Assessment</h3>
            <p className="text-sm text-gray-400 leading-relaxed">{result.assessment}</p>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Recommendations
            </h3>
            <ul className="space-y-1.5">
              {result.recommendations.map((rec, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-400"
                >
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Recent Verification Results */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h2 className="text-base font-semibold text-white">Recent Verification Results</h2>
        </div>
        <div className="divide-y divide-gray-800/60">
          {recent.map((r) => (
            <div key={r.id} className="px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{r.projectName}</p>
                <p className="text-xs text-gray-500">
                  {r.projectType} &middot; {r.country}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`text-lg font-bold ${
                    r.score >= 80
                      ? 'text-emerald-400'
                      : r.score >= 60
                      ? 'text-amber-400'
                      : 'text-red-400'
                  }`}
                >
                  {r.score}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium border ${
                    riskColor[r.riskLevel]
                  }`}
                >
                  {r.riskLevel}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    r.status === 'Verified'
                      ? 'text-emerald-400 bg-emerald-400/10'
                      : r.status === 'Pending'
                      ? 'text-amber-400 bg-amber-400/10'
                      : 'text-red-400 bg-red-400/10'
                  }`}
                >
                  {r.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
