"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { analyticsApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { OverchargePattern, HeatmapPoint } from "@/types";
import { BarChart3, MapPin, TrendingUp, AlertTriangle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const MapComponent = dynamic(() => import("@/components/analytics/HeatMap"), {
  ssr: false,
  loading: () => <div className="h-[400px] rounded-lg bg-muted animate-pulse" />,
});

const PIE_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

export default function AnalyticsPage() {
  const [overcharges, setOvercharges] = useState<OverchargePattern[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapPoint[]>([]);
  const [resolutionData, setResolutionData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.overcharges().catch(() => ({ data: { patterns: [] } })),
      analyticsApi.heatmap().catch(() => ({ data: { points: [] } })),
      analyticsApi.resolutionRates().catch(() => ({ data: { total_complaints: 0, by_status: {} } })),
    ])
      .then(([overRes, heatRes, resRes]) => {
        setOvercharges(overRes.data.patterns || []);
        setHeatmapData(heatRes.data.points || []);
        setResolutionData(resRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const sectionCounts: Record<string, { count: number; totalOvercharge: number }> = {};
  overcharges.forEach((p) => {
    if (!sectionCounts[p.section]) sectionCounts[p.section] = { count: 0, totalOvercharge: 0 };
    sectionCounts[p.section].count++;
    sectionCounts[p.section].totalOvercharge += p.overcharge;
  });
  const barData = Object.entries(sectionCounts)
    .map(([section, data]) => ({
      section: `Sec ${section}`,
      count: data.count,
      avgOvercharge: Math.round(data.totalOvercharge / data.count),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const pieData = resolutionData?.by_status
    ? Object.entries(resolutionData.by_status).map(([status, count]) => ({
        name: status,
        value: count as number,
      }))
    : [];

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" /> Transparency Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Anonymous, aggregated data showing overcharge patterns, complaint outcomes, and incident hotspots across India.
          </p>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-64 rounded-xl border bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="rounded-xl border bg-card p-4 text-center">
                <AlertTriangle className="h-6 w-6 mx-auto mb-2 text-orange-500" />
                <div className="text-2xl font-bold">{overcharges.length}</div>
                <div className="text-xs text-muted-foreground">Overcharges Detected</div>
              </div>
              <div className="rounded-xl border bg-card p-4 text-center">
                <TrendingUp className="h-6 w-6 mx-auto mb-2 text-blue-500" />
                <div className="text-2xl font-bold">{resolutionData?.total_complaints || 0}</div>
                <div className="text-xs text-muted-foreground">Total Complaints</div>
              </div>
              <div className="rounded-xl border bg-card p-4 text-center">
                <BarChart3 className="h-6 w-6 mx-auto mb-2 text-green-500" />
                <div className="text-2xl font-bold">{resolutionData?.resolution_rate || 0}%</div>
                <div className="text-xs text-muted-foreground">Resolution Rate</div>
              </div>
              <div className="rounded-xl border bg-card p-4 text-center">
                <MapPin className="h-6 w-6 mx-auto mb-2 text-purple-500" />
                <div className="text-2xl font-bold">{heatmapData.length}</div>
                <div className="text-xs text-muted-foreground">Incident Reports</div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Overcharge Patterns */}
              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-lg font-semibold mb-4">Top Overcharged Sections</h2>
                {barData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={barData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="section" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip
                        formatter={(value: number, name: string) =>
                          name === "avgOvercharge" ? formatCurrency(value) : value
                        }
                      />
                      <Bar dataKey="count" fill="#3b82f6" name="Overcharge Count" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
                    No overcharge data available yet
                  </div>
                )}
              </div>

              {/* Complaint Resolution */}
              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-lg font-semibold mb-4">Complaint Status Distribution</h2>
                {pieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {pieData.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
                    No complaint data available yet
                  </div>
                )}
              </div>
            </div>

            {/* Heatmap */}
            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" /> Incident Heatmap
              </h2>
              <MapComponent points={heatmapData} />
            </div>
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
