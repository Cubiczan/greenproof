// ── GreenVerify AI API Layer ──
// All calls target http://localhost:8000/api/* with fallback to demo data
import type {
  StatCards,
  Verification,
  VerificationScoreDistribution,
  CreditStandardDistribution,
  VerifyFormInput,
  VerifyResult,
  CreditNFT,
  MarketplaceListing,
  MarketplaceStats,
} from './types';
import {
  demoStats,
  demoVerifications,
  demoScoreDistribution,
  demoStandardDistribution,
  demoCreditNFTs,
  demoListings,
  demoMarketplaceStats,
} from './data';

const API_BASE = 'http://localhost:8000/api';

async function safeFetch<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

// ── Overview ──
export async function fetchStats(): Promise<StatCards> {
  return safeFetch<StatCards>(`${API_BASE}/stats`, demoStats);
}

export async function fetchRecentVerifications(): Promise<Verification[]> {
  return safeFetch<Verification[]>(`${API_BASE}/verifications`, demoVerifications);
}

export async function fetchScoreDistribution(): Promise<VerificationScoreDistribution[]> {
  return safeFetch<VerificationScoreDistribution[]>(`${API_BASE}/scores/distribution`, demoScoreDistribution);
}

export async function fetchStandardDistribution(): Promise<CreditStandardDistribution[]> {
  return safeFetch<CreditStandardDistribution[]>(`${API_BASE}/credits/standards`, demoStandardDistribution);
}

// ── Verify ──
export async function submitVerification(data: VerifyFormInput): Promise<VerifyResult> {
  try {
    const res = await fetch(`${API_BASE}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(30_000),
    });
    if (!res.ok) throw new Error('Verification request failed');
    return (await res.json()) as VerifyResult;
  } catch {
    // Return a simulated result
    return {
      success: true,
      score: Math.floor(Math.random() * 40) + 60,
      riskLevel: (['Low', 'Medium'] as const)[Math.floor(Math.random() * 2)],
      assessment:
        'Based on the AI analysis of the submitted documentation, this project demonstrates credible carbon reduction potential. The methodology aligns with the selected credit standard, and the baseline scenarios are well-defined. Additional monitoring data would strengthen the verification.',
      recommendations: [
        'Implement continuous monitoring of emission reductions',
        'Add third-party validation of baseline methodology',
        'Improve documentation of additionality criteria',
        'Consider updating to latest IPCC emission factors',
        'Strengthen leakage prevention measures',
      ],
      recommendedCreditAmount: Math.floor(data.estimatedAnnualCredits * (0.7 + Math.random() * 0.25)),
      pass: true,
    };
  }
}

// ── Credits ──
export async function fetchCreditNFTs(): Promise<CreditNFT[]> {
  return safeFetch<CreditNFT[]>(`${API_BASE}/credits`, demoCreditNFTs);
}

// ── Marketplace ──
export async function fetchListings(): Promise<MarketplaceListing[]> {
  return safeFetch<MarketplaceListing[]>(`${API_BASE}/marketplace/listings`, demoListings);
}

export async function fetchMarketplaceStats(): Promise<MarketplaceStats> {
  return safeFetch<MarketplaceStats>(`${API_BASE}/marketplace/stats`, demoMarketplaceStats);
}
