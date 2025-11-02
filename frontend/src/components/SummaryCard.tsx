"use client";
import { Card } from "@/components/ui/card";

export default function SummaryCard({ summaries }: { summaries: Record<string, string> }) {
  const entries = Object.entries(summaries || {});
  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">Section Summaries</h3>
      <div className="space-y-4">
        {entries.length === 0 && <p className="text-sm text-muted-foreground">No summaries available.</p>}
        {entries.map(([section, text]) => (
          <div key={section}>
            <h4 className="font-medium">{section}</h4>
            <p className="text-sm leading-6">{text}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
