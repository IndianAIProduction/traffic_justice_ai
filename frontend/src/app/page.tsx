"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Shield, Scale, FileSearch, BarChart3, ArrowRight } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";

const features = [
  {
    icon: Scale,
    title: "Legal Intelligence",
    description:
      "AI-powered legal guidance grounded in the Motor Vehicles Act. Know your rights instantly during any traffic stop.",
    href: "/legal-help",
  },
  {
    icon: FileSearch,
    title: "Challan Validation",
    description:
      "Upload your challan and verify fines against official schedules. Detect overcharges instantly.",
    href: "/challan",
  },
  {
    icon: Shield,
    title: "Evidence & Complaints",
    description:
      "Document misconduct with secure evidence upload. AI drafts formal complaints for grievance portals.",
    href: "/evidence",
  },
  {
    icon: BarChart3,
    title: "Transparency Dashboard",
    description:
      "Anonymous analytics showing overcharge patterns, misconduct hotspots, and complaint resolution rates.",
    href: "/analytics",
  },
];

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/legal-help");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero */}
        <section className="py-20 md:py-32 px-4">
          <div className="container mx-auto max-w-4xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm text-muted-foreground mb-6">
              <Shield className="h-4 w-4" />
              AI-Powered Legal Transparency
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Know Your Rights.
              <br />
              <span className="text-primary">Drive With Confidence.</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              Traffic Justice AI helps Indian drivers navigate traffic law enforcement with
              transparency. Validate challans, document misconduct, and file complaints &mdash;
              all powered by AI grounded in Indian traffic law.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition"
              >
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/analytics"
                className="inline-flex items-center justify-center gap-2 rounded-md border px-6 py-3 text-sm font-medium hover:bg-accent transition"
              >
                View Transparency Dashboard
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-20 px-4 bg-muted/30">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-3xl font-bold text-center mb-12">
              Four Pillars of Traffic Justice
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              {features.map((feature) => (
                <Link
                  key={feature.title}
                  href={feature.href}
                  className="group rounded-xl border bg-card p-6 hover:shadow-lg transition-all"
                >
                  <feature.icon className="h-10 w-10 text-primary mb-4" />
                  <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Trust */}
        <section className="py-20 px-4">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold mb-6">Built on Trust & Compliance</h2>
            <p className="text-muted-foreground mb-8">
              Traffic Justice AI encourages lawful compliance. We never help evade legitimate
              fines or encourage confrontation. All AI responses are grounded in actual Indian
              traffic law, with mandatory legal disclaimers.
            </p>
            <div className="grid grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold text-primary">100%</div>
                <div className="text-sm text-muted-foreground">RAG Grounded</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary">AES-256</div>
                <div className="text-sm text-muted-foreground">Evidence Encryption</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary">Full</div>
                <div className="text-sm text-muted-foreground">Audit Trail</div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
