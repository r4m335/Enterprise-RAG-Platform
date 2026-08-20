"use client";

import { useState, useEffect, useRef } from "react";
import { fetchClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type DocumentStatus = "UPLOADING" | "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED" | "DELETED";
type EmbeddingStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

interface Document {
  id: string;
  original_filename: string;
  file_size: number;
  processing_status: DocumentStatus;
  embedding_status: EmbeddingStatus;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    try {
      const data = await fetchClient("/api/v1/documents/");
      setDocuments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      await fetchClient("/api/v1/documents/", {
        method: "POST",
        body: formData,
      });
      // Immediately refetch
      fetchDocuments();
    } catch (e: any) {
      alert("Upload failed: " + e.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
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

  const getStatusDisplay = (doc: Document) => {
    if (doc.processing_status === "FAILED" || doc.embedding_status === "FAILED") {
      return <Badge variant="destructive">Failed</Badge>;
    }
    if (doc.processing_status === "UPLOADING" || doc.processing_status === "UPLOADED") {
      return <Badge variant="secondary">Uploading</Badge>;
    }
    if (doc.processing_status === "PROCESSING") {
      return <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-100">Processing</Badge>;
    }
    if (doc.processing_status === "COMPLETED") {
      if (doc.embedding_status === "PENDING" || doc.embedding_status === "PROCESSING") {
        return <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100">Indexing</Badge>;
      }
      if (doc.embedding_status === "COMPLETED") {
        return <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600">Ready</Badge>;
      }
    }
    return <Badge variant="outline">Unknown</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Documents</h2>
          <p className="text-zinc-500 dark:text-zinc-400">Manage your knowledge base documents.</p>
        </div>
        <div>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleUpload}
            accept=".pdf,.txt,.md,.docx"
          />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload Document"}
          </Button>
        </div>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-24 text-zinc-500">
                  Loading...
                </TableCell>
              </TableRow>
            ) : documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-24 text-zinc-500">
                  No documents found. Upload one to get started.
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell className="font-medium">{doc.original_filename}</TableCell>
                  <TableCell>{Math.round(doc.file_size / 1024)} KB</TableCell>
                  <TableCell>{new Date(doc.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>{getStatusDisplay(doc)}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700 hover:bg-red-50" onClick={() => handleDelete(doc.id)}>
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
