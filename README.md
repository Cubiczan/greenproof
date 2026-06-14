<div align="center">

# GreenProof

**AI-native carbon credit verification — on-chain and composable.** Verification scores are minted as on-chain credentials that any marketplace, registry, or compliance tool can query.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-ink!%205.0-orange?style=flat-square&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## The Problem

The voluntary carbon market is projected to reach **$2B by 2030**, but faces three critical trust problems:

1. **Slow verification** — Third-party audits take 6–18 months and cost $15K–$50K+ per project
2. **Trust deficit** — 10–30% of registry credits may represent limited real-world emission reductions ("ghost credits")
3. **Fragmented liquidity** — Credits are siloed across dozens of registries with no unified verification standard

Existing blockchain carbon credit projects verify off-chain and store results on-chain. **GreenProof flips this**: the AI verification verdict itself is a composable on-chain credential that any protocol can query, build on, and trust.

---

## What GreenProof Does

```
Project Documentation → AI Verification (Qwen LLM) → On-Chain Credential (PSP34 NFT)
                                                          ↓
                                              Marketplace (escrow trading)
                                                          ↓
                                              Composable API (any protocol can query)
```

1. **AI Verification** — Qwen LLM evaluates 7 criteria (additionality, permanence, measurability, leakage, methodology, documentation, compliance) and produces a structured 0–100 score with risk classification and actionable recommendations
2. **On-Chain Credential** — Verified credits are minted as PSP34 NFTs with rich metadata: project details, verification history, vintage year, credit standard
3. **Composable API** — Any marketplace, registry, or compliance tool can query verification scores via smart contract or REST API

---

## Why On-Chain Verification Scores?

| Off-Chain Verification (status quo) | On-Chain Verification (GreenProof) |
|---|---|
| Score lives in a PDF on a registry website | Score is a PSP34 NFT with structured metadata |
| Can't be queried programmatically | Any contract can call `get_verification_score()` |
| Trust depends on the registry's reputation | Trust is anchored in blockchain immutability |
| No composability — each marketplace re-verifies | Composable — one verification, many consumers |

---

## Dashboard

4 views: Platform Overview, AI Verification, Carbon Credits NFT Portfolio, Marketplace.

| View | What It Shows |
|------|--------------|
| **Overview** | Platform metrics, trend charts, recent activity |
| **AI Verification** | Submit projects, receive 0–100 scores with risk assessment |
| **Carbon Credits** | NFT portfolio with token ID, project, vintage, country, tx hash |
| **Marketplace** | Browse listings, buy with POT tokens, escrow-settled |

---

## Quick Start

```bash
git clone https://github.com/icohangar-ops/greenproof.git
cd greenproof

# Python backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src python -m greenverify.api.main

# Dashboard (http://localhost:3001)
cd dashboard && npm install && npm run dev

# Landing page (http://localhost:3002)
cd landing && npm install && npm run dev
```

Set `DASHSCOPE_API_KEY` to enable AI verification.

---

## Smart Contracts

### `carbon-credit` — PSP34 NFT

> **Build note:** `carbon-credit` implements the PSP34 NFT standard (ownership,
> approvals, total supply and the Enumerable extension) **natively** on
> `ink::storage::Mapping`, with no external framework. It builds on **stable
> Rust with ink! 5**, alongside `marketplace` and `verifier-registry`, and is a
> first-class member of the workspace. (It was previously built on OpenBrush
> 3.x, which required nightly Rust and ink! 4; that dependency has been removed.)

- **Standard**: PSP34 (ERC-721 equivalent) with a native Enumerable extension
- **Metadata**: Project name, verification date, verifier account, vintage year, credit standard (VCS/GS/CDM), country, project type
- **Operations**: `mint` (owner), `burn` (retirement), `transfer_credit`
- **Indexing**: Blake2x256 hash on project name

### `marketplace` — Escrow Trading

- Seller approves → `list(token_id, price)` → NFT into escrow
- Buyer → `buy(token_id)` with POT → NFT to buyer, POT to seller
- Events: `Listed`, `Sold`, `Delisted`

### `verifier-registry` — AI Verifier Management

- Register authorized AI verification agents
- Status management (active/suspended)
- Queries: `is_verifier()`, `get_all_verifiers()`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + LLM connectivity |
| `GET` | `/api/dashboard` | Platform overview metrics |
| `POST` | `/api/verify` | Submit project for AI verification |
| `GET` | `/api/credits` | List minted credit NFTs |
| `GET` | `/api/marketplace` | List marketplace listings |
| `POST` | `/api/marketplace/list` | Create listing |
| `POST` | `/api/marketplace/buy` | Purchase listing |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Blockchain | Portaldot / Substrate |
| Smart Contracts | Rust / ink! v5 (native PSP34, stable toolchain) |
| AI Backend | Python 3.11+ / FastAPI / Pydantic v2 |
| LLM | Qwen-plus (DashScope) with dual-region fallback |
| Frontend | Next.js 16 / React 19 / Tailwind CSS 4 |
| Charts | Recharts 3 |

---

## Project Structure

```
greenproof/
├── src/greenverify/
│   ├── api/main.py              # FastAPI entry point
│   ├── engines/verifier.py      # Verification orchestration
│   ├── models/carbon.py         # Pydantic v2 models
│   └── services/
│       ├── qwen_client.py       # Dual-region Qwen client
│       └── market_data.py       # Demo data service
├── contracts/
│   ├── carbon-credit/lib.rs     # PSP34 NFT
│   ├── marketplace/lib.rs       # Escrow marketplace
│   └── verifier-registry/lib.rs # Verifier management
├── dashboard/                   # Next.js 16 dashboard
├── landing/                     # Next.js 16 landing page
└── tests/                       # pytest suite
```

---

## Roadmap

- [ ] Multi-verifier consensus (3 AI verifiers must agree for mint)
- [ ] Oracle integration for real-world carbon project data
- [ ] Cross-chain bridge for Ethereum/Polygon compatibility
- [ ] Verifiable random verification agent selection
- [ ] Historical verification audit trail dashboard

---

## License

MIT. See [`LICENSE`](./LICENSE).

---

## CHP Governance

This repository is hardened with the [Consensus Hardening Protocol (CHP)](https://codeberg.org/cubiczan/consensus-hardening-protocol).

### Protocol Layers
- **R0 Gate**: Solvable, Scoped, Valid, Worth_it
- **Foundation Disclosure**: 1-3 weakest assumptions
- **Adversarial Layer**: Devil's advocate at Phase 0 and Round 3
- **State Machine**: EXPLORING → PROVISIONAL → PROVISIONAL_LOCK → LOCKED
- **Third-Party Validation**: Independent CONFIRM/REJECT before lock

### Domain Configuration
- **Category**: Blockchain / DeFi
- **Foundation Threshold**: 85
- **CFO Accuracy Guard**: Disabled

### CHP Version
cognitive-mesh-orchestrator 0.1.0 | [Protocol Docs](https://codeberg.org/cubiczan/consensus-hardening-protocol)
