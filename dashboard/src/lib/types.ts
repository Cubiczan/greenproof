// ── GreenVerify AI TypeScript Interfaces ──

export type ProjectType = 'Reforestation' | 'Renewable Energy' | 'Methane Capture' | 'Industrial';
export type CreditStandard = 'VCS' | 'Gold Standard' | 'CDM';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type VerificationStatus = 'Verified' | 'Pending' | 'Failed';

export interface StatCards {
  totalCreditsVerified: number;
  projectsVerified: number;
  activeListings: number;
  avgScore: number;
}

export interface Verification {
  id: string;
  projectName: string;
  projectType: ProjectType;
  country: string;
  score: number;
  riskLevel: RiskLevel;
  status: VerificationStatus;
  date: string;
}

export interface VerificationScoreDistribution {
  range: string;
  count: number;
}

export interface CreditStandardDistribution {
  name: CreditStandard;
  value: number;
  color: string;
}

export interface VerifyFormInput {
  projectName: string;
  description: string;
  projectType: ProjectType;
  country: string;
  vintageYear: number;
  estimatedAnnualCredits: number;
  creditStandard: CreditStandard;
  documentation: string;
}

export interface VerifyResult {
  success: boolean;
  score: number;
  riskLevel: RiskLevel;
  assessment: string;
  recommendations: string[];
  recommendedCreditAmount: number;
  pass: boolean;
}

export interface CreditNFT {
  tokenId: string;
  projectName: string;
  creditAmount: number;
  vintageYear: number;
  creditStandard: CreditStandard;
  country: string;
  ownerAddress: string;
  mintedDate: string;
  txHash: string;
  projectType: ProjectType;
}

export interface MarketplaceListing {
  tokenId: string;
  projectName: string;
  creditAmount: number;
  pricePOT: number;
  sellerAddress: string;
  listedDate: string;
  creditStandard: CreditStandard;
  projectType: ProjectType;
  vintageYear: number;
}

export interface MarketplaceStats {
  totalVolumeTraded: number;
  numberOfTrades: number;
  floorPrice: number;
  avgPrice: number;
}
