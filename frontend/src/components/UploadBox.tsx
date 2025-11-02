"use client";
import React, { useState } from "react";
import api from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import toast from "react-hot-toast";

type Props = { onUploaded: (fileId: string) => void };

export default function UploadBox({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>("");

  const handleUpload = async () => {
    if (!file) return toast.error("Choose a PDF first");
    try {
      const init = await api.post(`/upload/init?filename=${encodeURIComponent(file.name)}`);
      const fileId = init.data.file_id as string;

      const fd = new FormData();
      fd.append("file", file);
      await api.post("/upload/chunk", fd, {
        headers: { "X-File-Id": fileId, "X-Chunk-Index": 0, "X-Total-Chunks": 1 },
        onUploadProgress: (p) => { if (p.total) setProgress(Math.round((p.loaded / p.total) * 100)); },
      });

      await api.post("/upload/complete", { file_id: fileId, filename: file.name, total_chunks: 1 });

      toast.success("Uploaded! Processing…");
      setStatus("assembled");
      onUploaded(fileId);
    } catch (e) {
      console.error(e);
      toast.error("Upload failed");
    }
  };

  return (
    <Card className="p-6 space-y-4">
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <Button onClick={handleUpload}>Upload</Button>
      <Progress value={progress} />
      <p className="text-sm text-muted-foreground">Status: {status || "—"}</p>
    </Card>
  );
}
