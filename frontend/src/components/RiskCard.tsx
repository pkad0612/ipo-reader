"use client";
import { Card } from "@/components/ui/card";
type Neg = { sentence: string; negative: number };
type Props = { score: number; avgPos: number; avgNeg: number; avgNeu: number; negatives: Neg[] };

export default function RiskCard({ score, avgPos, avgNeg, avgNeu, negatives }: Props) {
  return (
    <Card className="p-6 space-y-4">
      <h3 className="text-lg font-semibold">Narrative Risk</h3>
      <div className="text-4xl font-bold">{score}</div>
      <p className="text-sm text-muted-foreground">Avg pos: {avgPos} · Avg neg: {avgNeg} · Avg neu: {avgNeu}</p>
      <div className="space-y-2">
        <h4 className="font-medium">Top negative sentences</h4>
        <ul className="list-disc pl-5 space-y-1">
          {negatives?.slice(0,5).map((n, i) => (<li key={i} className="text-sm">{n.sentence}</li>))}
        </ul>
      </div>
    </Card>
  );
}
