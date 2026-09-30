"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { fetchClient, uploadFileWithProgress } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { 
  DocumentTableStatus, 
  type DocumentProcessingState 
} from "@/components/document-progress-tracker";
import { FileUp, Loader2, RefreshCw } from "lucide-react";

type DocumentStatus = "UPLOADING" | "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED" | "DELETED";
type EmbeddingStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

interface Document {
  id: string;
  original_filename: string;
  file_size: number;
  processing_status: DocumentStatus;
  embedding_status: EmbeddingStatus;
  created_at: string;
  processing_error?: string;
  embedding_error?: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [activeUploadState, setActiveUploadState] = useState<DocumentProcessingState | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data: Document[] = await fetchClient("/api/v1/documents/");
      setDocuments(data);
    } catch (e) {
      // Ignore network errors
    } finally {
      setLoading(false);
    }
  }, []);

  // Dynamic Polling: Fast (1.5s) when processing or uploading; normal (6s) when idle
  useEffect(() => {
    fetchDocuments();

    const hasActiveTask =
      uploading ||
      documents.some(
        (d) =>
          d.embedding_status !== "COMPLETED" &&
          d.processing_status !== "FAILED" &&
          d.embedding_status !== "FAILED"
      );

    const pollInterval = hasActiveTask ? 1500 : 6000;
    const interval = setInterval(fetchDocuments, pollInterval);
    return () => clearInterval(interval);
  }, [fetchDocuments, uploading, documents]);

  const processFile = async (file: File) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const startTime = Date.now();
    setActiveUploadState({
      filename: file.name,
      fileSize: file.size,
      uploadPercent: 10,
      isUploading: true,
      startedAt: startTime,
    });
    setUploading(true);

    try {
      await uploadFileWithProgress<{ message: string; document_id: string }>(
        "/api/v1/documents/",
        formData,
        (percent) => {
          setActiveUploadState((prev) =>
            prev ? { ...prev, uploadPercent: Math.max(10, percent) } : null
          );
        }
      );

      // Once uploaded to server, clear optimistic state and refresh documents table
      setActiveUploadState(null);
      await fetchDocuments();
    } catch (e: any) {
      setActiveUploadState(null);
      alert("Upload failed: " + e.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processFile(file);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await fetchClient(`/api/v1/documents/${id}`, { method: "DELETE" });
      fetchDocuments();
    } catch (e: any) {
      alert("Delete failed: " + e.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            Documents
          </h2>
          <p className="text-zinc-500 dark:text-zinc-400 text-sm">
            Upload files to parse, chunk, and index into your vector knowledge base.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleUpload}
            accept=".pdf,.txt,.md,.docx"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="gap-2 shadow-xs cursor-pointer"
          >
            <FileUp className="w-4 h-4" />
            <span>{uploading ? "Uploading..." : "Upload Document"}</span>
          </Button>
        </div>
      </div>

      {/* Documents Table */}
      <Card className="overflow-hidden shadow-xs">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[30%]">Name</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead className="w-[35%]">Status & Progress</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {/* Optimistic upload row while file bytes are being transferred */}
            {activeUploadState && activeUploadState.isUploading && (
              <TableRow className="bg-blue-50/30 dark:bg-blue-950/20">
                <TableCell className="font-medium">
                  <span className="truncate max-w-[240px] md:max-w-[360px]" title={activeUploadState.filename}>
                    {activeUploadState.filename}
                  </span>
                </TableCell>
                <TableCell className="text-zinc-500 font-mono text-xs">
                  {Math.round(activeUploadState.fileSize / 1024)} KB
                </TableCell>
                <TableCell className="text-zinc-500 text-xs">
                  Just now
                </TableCell>
                <TableCell>
                  <div className="w-48 sm:w-56 space-y-1.5 py-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                        <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
                        <span>Uploading...</span>
                      </span>
                      <span className="font-mono text-[11px] text-zinc-500 dark:text-zinc-400">
                        {activeUploadState.uploadPercent}%
                      </span>
                    </div>
                    <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 transition-all duration-300 ease-out relative overflow-hidden"
                        style={{ width: `${activeUploadState.uploadPercent}%` }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-xs text-zinc-400 italic">Uploading</span>
                </TableCell>
              </TableRow>
            )}

            {loading && documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-28 text-zinc-500">
                  <div className="flex items-center justify-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-zinc-400" />
                    <span>Loading documents...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : documents.length === 0 && !activeUploadState ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-28 text-zinc-500">
                  No documents found. Click &quot;Upload Document&quot; above to get started.
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow key={doc.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/50">
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <span className="truncate max-w-[240px] md:max-w-[360px]" title={doc.original_filename}>
                        {doc.original_filename}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-zinc-500 font-mono text-xs">
                    {Math.round(doc.file_size / 1024)} KB
                  </TableCell>
                  <TableCell className="text-zinc-500 text-xs">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <DocumentTableStatus document={doc} />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs h-8 cursor-pointer"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
