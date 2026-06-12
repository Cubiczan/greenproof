import Image from "next/image";
import {
  ShieldAlert,
  Copy,
  Eye,
  Brain,
  Link2,
  ShoppingCart,
  FileUp,
  ScanSearch,
  Stamp,
  ArrowRightLeft,
  ExternalLink,
  Trophy,
  Calendar,
  DollarSign,
  ChevronRight,
} from "lucide-react";

function GithubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

/* ───────────────────────── NAV ───────────────────────── */
function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-emerald-950/60 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="GreenVerify AI" width={32} height={32} />
          <span className="text-lg font-semibold tracking-tight text-white">
            GreenVerify AI
          </span>
        </div>
        <div className="hidden items-center gap-8 md:flex">
          <a href="#problem" className="text-sm text-zinc-400 transition-colors hover:text-emerald-400">
            Problem
          </a>
          <a href="#solution" className="text-sm text-zinc-400 transition-colors hover:text-emerald-400">
            Solution
          </a>
          <a href="#how-it-works" className="text-sm text-zinc-400 transition-colors hover:text-emerald-400">
            How It Works
          </a>
          <a href="#tech" className="text-sm text-zinc-400 transition-colors hover:text-emerald-400">
            Tech Stack
          </a>
          <a href="#demo" className="text-sm text-zinc-400 transition-colors hover:text-emerald-400">
            Demo
          </a>
        </div>
        <a
          href="https://github.com/icohangar-ops/greenverify-ai"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 rounded-lg border border-emerald-800 bg-emerald-950/50 px-3 py-1.5 text-sm font-medium text-emerald-400 transition-colors hover:border-emerald-600 hover:bg-emerald-900/50"
        >
          <GithubIcon className="h-4 w-4" />
          GitHub
        </a>
      </div>
    </nav>
  );
}

/* ───────────────────────── HERO ───────────────────────── */
function HeroSection() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-20">
      {/* Background gradient orbs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-32 top-1/4 h-[500px] w-[500px] rounded-full bg-emerald-600/10 blur-[120px]" />
        <div className="absolute -right-32 bottom-1/4 h-[400px] w-[400px] rounded-full bg-emerald-500/8 blur-[100px]" />
        <div className="absolute left-1/2 top-0 h-[300px] w-[600px] -translate-x-1/2 rounded-full bg-emerald-700/6 blur-[100px]" />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(16,185,129,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.5) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <Image
          src="/logo.png"
          alt="GreenVerify AI"
          width={80}
          height={80}
          className="mx-auto mb-8"
        />
        <h1 className="mb-4 text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
          GreenVerify{" "}
          <span className="bg-gradient-to-r from-emerald-400 to-emerald-600 bg-clip-text text-transparent">
            AI
          </span>
        </h1>
        <p className="mb-6 text-xl font-medium text-emerald-300/90 sm:text-2xl">
          AI-Powered Carbon Credit Verification &amp; Trading on Portaldot
        </p>
        <p className="mx-auto mb-10 max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">
          GreenVerify combines Alibaba Cloud Qwen LLM with Portaldot blockchain
          to bring trust, transparency, and AI intelligence to the voluntary
          carbon market. Submit carbon projects for AI-powered verification, mint
          verified credits as on-chain NFTs, and trade them on a decentralized
          marketplace.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href="#demo"
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-emerald-900/40 transition-all hover:bg-emerald-500 hover:shadow-emerald-900/60"
          >
            View Demo
            <ChevronRight className="h-4 w-4" />
          </a>
          <a
            href="https://github.com/icohangar-ops/greenverify-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-900/60 px-8 py-3.5 text-base font-semibold text-zinc-300 transition-all hover:border-emerald-700 hover:bg-zinc-800/60 hover:text-emerald-400"
          >
            <GithubIcon className="h-5 w-5" />
            GitHub Repo
          </a>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="h-6 w-6 rounded-full border-2 border-emerald-600/50" />
      </div>
    </section>
  );
}

/* ───────────────────────── PROBLEM ───────────────────────── */
const problems = [
  {
    icon: ShieldAlert,
    title: "Verification Gap",
    description:
      "Manual verification takes 6-18 months, costs $10K-50K per project — creating a massive bottleneck in the voluntary carbon market.",
  },
  {
    icon: Copy,
    title: "Double Counting",
    description:
      "Same credits sold multiple times across registries. Without a single source of truth, fraud erodes market confidence.",
  },
  {
    icon: Eye,
    title: "No Transparency",
    description:
      "Buyers can't verify credit quality or project impact. Opaque processes lead to greenwashing and misallocated capital.",
  },
];

function ProblemSection() {
  return (
    <section id="problem" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-500">
            The Problem
          </p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            The Carbon Market Needs Trust
          </h2>
          <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-emerald-600" />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {problems.map((item) => (
            <div
              key={item.title}
              className="group rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-red-900/40 hover:bg-red-950/10 sm:p-8"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-red-950/50 text-red-400 transition-colors group-hover:bg-red-900/50">
                <item.icon className="h-6 w-6" />
              </div>
              <h3 className="mb-3 text-xl font-semibold text-white">{item.title}</h3>
              <p className="text-sm leading-relaxed text-zinc-400">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── SOLUTION ───────────────────────── */
const solutions = [
  {
    icon: Brain,
    title: "AI-Powered Verification",
    description:
      "Qwen LLM analyzes project documentation, scoring credits on a 0-100 scale with comprehensive risk assessment and detailed recommendations.",
  },
  {
    icon: Link2,
    title: "Onchain Carbon Credits",
    description:
      "Verified credits minted as PSP34 NFTs on Portaldot, fully traceable and tamper-proof with immutable provenance records.",
  },
  {
    icon: ShoppingCart,
    title: "Decentralized Marketplace",
    description:
      "Trade verified carbon credits in POT, Portaldot's native token, with zero intermediaries and full transparency.",
  },
];

function SolutionSection() {
  return (
    <section id="solution" className="relative py-24 sm:py-32">
      {/* Subtle background accent */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-emerald-950/10 to-transparent" />

      <div className="relative mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-500">
            The Solution
          </p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            AI Verification + Onchain Integrity
          </h2>
          <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-emerald-600" />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {solutions.map((item, idx) => (
            <div
              key={item.title}
              className="group relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-emerald-800/60 hover:bg-emerald-950/20 sm:p-8"
            >
              {/* Corner accent */}
              <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-emerald-600/5 transition-colors group-hover:bg-emerald-600/10" />

              <div className="relative">
                <div className="mb-1 text-xs font-semibold text-emerald-600">
                  0{idx + 1}
                </div>
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-950/80 text-emerald-400 transition-colors group-hover:bg-emerald-900/60">
                  <item.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-white">
                  {item.title}
                </h3>
                <p className="text-sm leading-relaxed text-zinc-400">
                  {item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── ARCHITECTURE ───────────────────────── */
const steps = [
  {
    num: 1,
    icon: FileUp,
    title: "Submit",
    description:
      "Carbon project documentation is submitted through the dashboard for AI analysis.",
  },
  {
    num: 2,
    icon: ScanSearch,
    title: "Verify",
    description:
      "AI analyzes documentation, scoring the project and recommending credit amount.",
  },
  {
    num: 3,
    icon: Stamp,
    title: "Mint",
    description:
      "Verified credits are minted as NFTs on the Portaldot blockchain.",
  },
  {
    num: 4,
    icon: ArrowRightLeft,
    title: "Trade",
    description:
      "Credits are listed on the decentralized marketplace for trading in POT.",
  },
];

function ArchitectureSection() {
  return (
    <section id="how-it-works" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-500">
            Architecture
          </p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            How It Works
          </h2>
          <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-emerald-600" />
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, idx) => (
            <div key={step.title} className="relative text-center">
              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div className="absolute left-1/2 top-8 hidden h-px w-full bg-gradient-to-r from-emerald-700/40 to-transparent lg:block" />
              )}

              <div className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-800/50 bg-emerald-950/40 text-emerald-400">
                <step.icon className="h-7 w-7" />
                <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white">
                  {step.num}
                </span>
              </div>
              <h3 className="mb-2 text-lg font-semibold text-white">{step.title}</h3>
              <p className="text-sm leading-relaxed text-zinc-400">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── TECH STACK ───────────────────────── */
const techStack = [
  { name: "Portaldot", sub: "Substrate Chain", color: "emerald" },
  { name: "Rust / ink!", sub: "Smart Contracts", color: "orange" },
  { name: "Python / FastAPI", sub: "Backend & AI Engine", color: "blue" },
  { name: "Qwen LLM", sub: "AI Verification", color: "violet" },
  { name: "Next.js", sub: "Dashboard Frontend", color: "zinc" },
  { name: "Pydantic v2", sub: "Data Validation", color: "amber" },
];

const colorMap: Record<string, string> = {
  emerald: "border-emerald-800/50 bg-emerald-950/30 text-emerald-400",
  orange: "border-orange-800/50 bg-orange-950/30 text-orange-400",
  blue: "border-blue-800/50 bg-blue-950/30 text-blue-400",
  violet: "border-violet-800/50 bg-violet-950/30 text-violet-400",
  zinc: "border-zinc-700/50 bg-zinc-800/30 text-zinc-300",
  amber: "border-amber-800/50 bg-amber-950/30 text-amber-400",
};

function TechStackSection() {
  return (
    <section id="tech" className="relative py-24 sm:py-32">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-emerald-950/10 to-transparent" />

      <div className="relative mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-500">
            Technology
          </p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            Built With
          </h2>
          <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-emerald-600" />
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {techStack.map((tech) => (
            <div
              key={tech.name}
              className={`flex flex-col items-center rounded-xl border p-5 transition-all hover:scale-105 ${colorMap[tech.color]}`}
            >
              <span className="text-sm font-semibold">{tech.name}</span>
              <span className="mt-1 text-xs opacity-60">{tech.sub}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── DEMO ───────────────────────── */
const demoScreenshots = [
  { name: "Dashboard Overview", file: "01-overview.png" },
  { name: "AI Verification", file: "02-verify.png" },
  { name: "Carbon Credits", file: "03-credits.png" },
  { name: "Marketplace", file: "04-marketplace.png" },
];

function DemoSection() {
  return (
    <section id="demo" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-emerald-500">
            Live Demo
          </p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
            Live Dashboard
          </h2>
          <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-emerald-600" />
          <p className="mx-auto mt-4 max-w-xl text-zinc-400">
            A fully functional web dashboard to submit projects, run AI
            verification, manage credits, and trade on the decentralized
            marketplace.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          {demoScreenshots.map((shot) => (
            <div
              key={shot.file}
              className="group overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50 transition-all hover:border-emerald-800/40"
            >
              {/* Placeholder */}
              <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-zinc-800/60 to-zinc-900/60 p-8">
                <div className="text-center">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-950/60 text-emerald-600">
                    <ExternalLink className="h-5 w-5" />
                  </div>
                  <p className="text-sm font-medium text-zinc-400">
                    {shot.name}
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">{shot.file}</p>
                </div>
              </div>
              <div className="border-t border-zinc-800 px-5 py-3">
                <p className="text-sm font-medium text-zinc-300">{shot.name}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── HACKATHON ───────────────────────── */
function HackathonSection() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-emerald-950/10 to-transparent" />

      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-800/60 bg-emerald-950/40 px-4 py-1.5">
          <Trophy className="h-4 w-4 text-emerald-400" />
          <span className="text-sm font-medium text-emerald-300">
            Hackathon Project
          </span>
        </div>

        <h2 className="mb-6 text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
          Built for Portaldot Hackathon S1
        </h2>

        <div className="mx-auto mb-10 max-w-md rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 sm:p-8">
          <div className="mb-5 flex flex-wrap items-center justify-center gap-3">
            <span className="inline-flex items-center rounded-lg border border-amber-800/40 bg-amber-950/30 px-3 py-1.5 text-sm font-medium text-amber-400">
              <Trophy className="mr-1.5 h-3.5 w-3.5" />
              DoraHacks Portaldot Online Mini Hackathon S1
            </span>
          </div>
          <div className="mb-5 flex flex-wrap items-center justify-center gap-3">
            <span className="inline-flex items-center rounded-lg border border-violet-800/40 bg-violet-950/30 px-3 py-1.5 text-sm font-medium text-violet-400">
              <Brain className="mr-1.5 h-3.5 w-3.5" />
              AI-Powered Onchain Workflows
            </span>
          </div>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <DollarSign className="h-4 w-4 text-emerald-500" />
              <span>
                <strong className="text-white">$3,500 USDT</strong> Prize Pool
              </span>
            </div>
            <div className="hidden h-3 w-px bg-zinc-800 sm:block" />
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Calendar className="h-4 w-4 text-emerald-500" />
              <span>
                <strong className="text-white">May 4–31, 2026</strong>
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────────── FOOTER ───────────────────────── */
function Footer() {
  return (
    <footer className="mt-auto border-t border-zinc-800/60 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
        <p className="text-sm text-zinc-500">
          GreenVerify AI —{" "}
          <span className="text-zinc-400">MIT License</span>
        </p>
        <div className="flex items-center gap-6">
          <a
            href="https://github.com/icohangar-ops/greenverify-ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-emerald-400"
          >
            <GithubIcon className="h-4 w-4" />
            GitHub
          </a>
          <a
            href="https://dorahacks.io"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-emerald-400"
          >
            <ExternalLink className="h-4 w-4" />
            DoraHacks
          </a>
          <a
            href="https://docs.portaldot.io"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-emerald-400"
          >
            <ExternalLink className="h-4 w-4" />
            Portaldot Docs
          </a>
        </div>
      </div>
    </footer>
  );
}

/* ───────────────────────── PAGE ───────────────────────── */
export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Navbar />
      <main className="flex-1">
        <HeroSection />
        <ProblemSection />
        <SolutionSection />
        <ArchitectureSection />
        <TechStackSection />
        <DemoSection />
        <HackathonSection />
      </main>
      <Footer />
    </div>
  );
}
