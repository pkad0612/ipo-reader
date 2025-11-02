"use client";
import React, { useState } from "react";
import api from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function QACard({ fileId }: { fileId: string }) {
  const [q, setQ] = useState("");
  const [ans, setAns] = useState<string | null>(null);
  const [ctx, setCtx] = useState<any[]>([]);
  const ask = async () => {
    const { data } = await api.post("/qa", { file_id: fileId, query: q });
    setAns(data.answer);
    setCtx(data.context || []);
  };
  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">Ask a Question</h3>
      <Textarea placeholder="e.g., What are the objects of the issue?" value={q} onChange={(e) => setQ(e.target.value)} />
      <Button onClick={ask} disabled={!q.trim()}>Ask</Button>
      {ans && (
        <div className="space-y-2">
          <h4 className="font-medium">Answer</h4>
          <p className="text-sm">{ans}</p>
          <h4 className="font-medium mt-3">Top Context</h4>
          <ul className="list-disc pl-5 space-y-1">
            {ctx.slice(0,3).map((c, i) => (
              <li key={i} className="text-xs text-muted-foreground"><b>{c.section}</b>: {c.text?.slice(0,180)}…</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
