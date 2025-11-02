"use client";

import { useEffect, useState } from "react";
import UploadBox from "@/components/UploadBox";
import RiskCard from "@/components/RiskCard";
import SummaryCard from "@/components/SummaryCard";
import QACard from "@/components/QACard";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";

type RiskResp = {
  risk_score: number;
  avg_positive: number;
  avg_negative: number;
  avg_neutral: number;
  top_negatives: { sentence: string; negative: number }[];
};

export default function Home() {
  const [fileId, setFileId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [risk, setRisk] = useState<RiskResp | null>(null);
  const [summaries, setSummaries] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ⏳ Poll backend for file status
  useEffect(() => {
    if (!fileId) return;
    setError(null);
    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/status/${fileId}`);
        setStatus(data.status);
        if (data.status === "done" || data.status === "error") {
          clearInterval(interval);
        }
      } catch (e) {
        setError("Failed to fetch file status.");
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [fileId]);

  // 📊 Fetch risk & summary once done
  useEffect(() => {
    const fetchInsights = async () => {
      if (!fileId || status !== "done") return;
      setLoading(true);
      try {
        const [riskRes, summaryRes] = await Promise.all([
          api.post("/risk", { file_id: fileId }),
          api.post("/summary", { file_id: fileId }),
        ]);
        setRisk(riskRes.data);
        setSummaries(summaryRes.data.summaries || {});
      } catch (err) {
        console.error(err);
        setError("Error loading insights. Please retry.");
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, [fileId, status]);

  return (
    <main className="min-h-screen p-6 md:p-10 bg-gray-50">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">📊 AI IPO Prospectus Reader</h1>
          <Button asChild variant="outline">
            <a href="/compare">Go to Compare →</a>
          </Button>
        </div>

        <UploadBox
          onUploaded={(id) => {
            setFileId(id);
            setStatus("assembled");
            setRisk(null);
            setSummaries({});
            setError(null);
          }}
        />

        {fileId && (
          <p className="text-sm text-muted-foreground">
            File ID: <b>{fileId}</b> · Status:{" "}
            <span
              className={
                status === "done"
                  ? "text-green-600 font-medium"
                  : status === "error"
                  ? "text-red-600 font-medium"
                  : "text-blue-600 font-medium"
              }
            >
              {status || "waiting"}
            </span>
          </p>
        )}

        {error && (
          <div className="p-4 rounded-md bg-red-100 text-red-700 border border-red-300">
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div className="p-4 rounded-md bg-yellow-50 border border-yellow-200 text-yellow-700 text-sm">
            ⏳ Generating risk and summary insights...
          </div>
        )}

        {status === "done" && !loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {risk && (
              <RiskCard
                score={risk.risk_score}
                avgPos={risk.avg_positive}
                avgNeg={risk.avg_negative}
                avgNeu={risk.avg_neutral}
                negatives={risk.top_negatives}
              />
            )}
            <SummaryCard summaries={summaries} />
          </div>
        )}

        {status === "done" && fileId && !loading && (
          <QACard fileId={fileId} />
        )}
      </div>
    </main>
  );
}
