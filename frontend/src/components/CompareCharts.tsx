"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend
} from "recharts";
import { Card } from "@/components/ui/card";

type Props = {
  ipoA: { name: string; risk_score: number; avg_positive: number; avg_negative: number; avg_neutral: number };
  ipoB: { name: string; risk_score: number; avg_positive: number; avg_negative: number; avg_neutral: number };
};

export default function CompareCharts({ ipoA, ipoB }: Props) {
  const barData = [
    { metric: "Risk Score", [ipoA.name]: ipoA.risk_score, [ipoB.name]: ipoB.risk_score },
    { metric: "Avg Negative", [ipoA.name]: ipoA.avg_negative, [ipoB.name]: ipoB.avg_negative },
  ];

  const radarData = [
    { metric: "Positive", [ipoA.name]: ipoA.avg_positive, [ipoB.name]: ipoB.avg_positive },
    { metric: "Negative", [ipoA.name]: ipoA.avg_negative, [ipoB.name]: ipoB.avg_negative },
    { metric: "Neutral",  [ipoA.name]: ipoA.avg_neutral,  [ipoB.name]: ipoB.avg_neutral  },
  ];

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card className="p-4">
        <h3 className="font-semibold mb-3">📊 Risk Comparison</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={barData}>
            <XAxis dataKey="metric" />
            <YAxis />
            <Tooltip />
            <Bar dataKey={ipoA.name} fill="#2563eb" />
            <Bar dataKey={ipoB.name} fill="#16a34a" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-4">
        <h3 className="font-semibold mb-3">🧠 Sentiment Radar</h3>
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis />
            <Radar name={ipoA.name} dataKey={ipoA.name} stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
            <Radar name={ipoB.name} dataKey={ipoB.name} stroke="#16a34a" fill="#16a34a" fillOpacity={0.4} />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
