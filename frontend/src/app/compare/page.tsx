"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import CompareCharts from "@/components/CompareCharts";

type FileRow = { file_id: string; filename: string; status: string; updated_at: string };
type CompareResp = {
  ipo_1: {
    file_id: string;
    risk_score: number;
    avg_positive?: number;
    avg_negative: number;
    avg_neutral?: number;
    summary: Record<string, string>;
  };
  ipo_2: {
    file_id: string;
    risk_score: number;
    avg_positive?: number;
    avg_negative: number;
    avg_neutral?: number;
    summary: Record<string, string>;
  };
  comparison: { higher_risk: string; risk_gap: number };
};

export default function ComparePage() {
  const [files, setFiles] = useState<FileRow[]>([]);
  const [a, setA] = useState<string>("");
  const [b, setB] = useState<string>("");
  const [result, setResult] = useState<CompareResp | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch all processed IPOs
  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/files?status=done&limit=50");
        setFiles(data.files);
        if (data.files.length >= 2) {
          setA(data.files[0].file_id);
          setB(data.files[1].file_id);
        }
      } catch (err) {
        console.error("Error fetching files:", err);
      }
    })();
  }, []);

  // Compare two IPOs
  const handleCompare = async () => {
    if (!a || !b || a === b) return;
    setLoading(true);
    try {
      const { data } = await api.post("/compare", { file_id_1: a, file_id_2: b });
      setResult(data);
    } catch (err) {
      console.error("Error comparing:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">🆚 Compare IPOs</h1>
          <Button asChild variant="outline">
            <a href="/">← Back to Dashboard</a>
          </Button>
        </div>

        {/* Selection panel */}
        <Card className="p-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-1">Select IPO A</h4>
              <select
                value={a}
                onChange={(e) => setA(e.target.value)}
                className="w-full border rounded-md p-2 bg-white"
              >
                {files.map((f) => (
                  <option key={f.file_id} value={f.file_id}>
                    {f.filename} ({f.file_id.slice(0, 6)}…)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <h4 className="font-medium mb-1">Select IPO B</h4>
              <select
                value={b}
                onChange={(e) => setB(e.target.value)}
                className="w-full border rounded-md p-2 bg-white"
              >
                {files.map((f) => (
                  <option key={f.file_id} value={f.file_id}>
                    {f.filename} ({f.file_id.slice(0, 6)}…)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Button onClick={handleCompare} disabled={!a || !b || a === b || loading}>
            {loading ? "Comparing..." : "Compare IPOs"}
          </Button>
        </Card>

        {/* Comparison results */}
        {result && (
          <>
            <div className="grid md:grid-cols-2 gap-6">
              {/* IPO A */}
              <Card className="p-6 space-y-3">
                <h2 className="font-semibold text-lg">IPO A</h2>
                <p>Risk Score: <b>{result.ipo_1.risk_score}</b></p>
                <p>Avg Negative: {result.ipo_1.avg_negative.toFixed(3)}</p>
                <div>
                  <h4 className="font-medium mt-3">Key Summaries</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {Object.entries(result.ipo_1.summary).slice(0, 4).map(([k, v]) => (
                      <li key={k}><b>{k}:</b> {v.slice(0, 120)}...</li>
                    ))}
                  </ul>
                </div>
              </Card>

              {/* IPO B */}
              <Card className="p-6 space-y-3">
                <h2 className="font-semibold text-lg">IPO B</h2>
                <p>Risk Score: <b>{result.ipo_2.risk_score}</b></p>
                <p>Avg Negative: {result.ipo_2.avg_negative.toFixed(3)}</p>
                <div>
                  <h4 className="font-medium mt-3">Key Summaries</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {Object.entries(result.ipo_2.summary).slice(0, 4).map(([k, v]) => (
                      <li key={k}><b>{k}:</b> {v.slice(0, 120)}...</li>
                    ))}
                  </ul>
                </div>
              </Card>

              {/* Comparison insight */}
              <Card className="p-6 md:col-span-2 space-y-2">
                <h3 className="font-semibold text-lg">📈 Comparison Insights</h3>
                <p>
                  Higher Risk:{" "}
                  <b className="text-red-600">{result.comparison.higher_risk.slice(0, 6)}...</b>
                  {" "} | Risk Gap: <b>{result.comparison.risk_gap}</b>
                </p>
              </Card>
            </div>

            {/* Charts Section */}
            <CompareCharts
              ipoA={{
                name: "IPO A",
                risk_score: result.ipo_1.risk_score,
                avg_positive: result.ipo_1.avg_positive ?? 0.3,
                avg_negative: result.ipo_1.avg_negative,
                avg_neutral: result.ipo_1.avg_neutral ?? 0.5,
              }}
              ipoB={{
                name: "IPO B",
                risk_score: result.ipo_2.risk_score,
                avg_positive: result.ipo_2.avg_positive ?? 0.3,
                avg_negative: result.ipo_2.avg_negative,
                avg_neutral: result.ipo_2.avg_neutral ?? 0.5,
              }}
            />
          </>
        )}
      </div>
    </main>
  );
}
