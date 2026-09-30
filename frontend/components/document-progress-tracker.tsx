"use client";

import React, { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Sparkles, 
  Database, 
  ArrowRight, 
  X,
  Clock,
  Layers
} from "lucide-react";
import Link from "next/link";

export type DocumentProcessingState = {
  id?: string;
  filename: string;
  fileSize: number;
  uploadPercent: number; // 0 - 100
  isUploading: boolean;
  processing_status?: string; // "UPLOADING" | "PROCESSING" | "COMPLETED" | "FAILED"
  embedding_status?: string;  // "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  error?: string;
  startedAt: number; // timestamp ms
  completedAt?: number;
};

// Calculate estimated total seconds for upload + text parsing + vector indexing
export function getEstimatedTotalSeconds(fileSizeBytes: number = 100_000): number {
  // Base cold start & celery queue ~4s, + 2.5s per 150KB
  const baseSec = 4.5;
  const sizeFactor = Math.min(22, (fileSizeBytes / (150 * 1024)) * 2.5);
  return Math.max(5, Math.round(baseSec + sizeFactor));
}

// Compute percentage (0 - 100), remaining seconds, and human readable stage
export function computeProgressDetails(state: DocumentProcessingState) {
  const isFailed = state.processing_status === "FAILED" || state.embedding_status === "FAILED";
  if (isFailed) {
    return {
      percent: 100,
      stageName: "Failed",
      subtext: state.error || "An error occurred during processing",
      remainingSec: 0,
      currentStepIndex: -1,
      isCompleted: false,
      isFailed: true,
    };
  }

  const isCompleted = state.processing_status === "COMPLETED" && state.embedding_status === "COMPLETED";
  if (isCompleted) {
    const totalTimeSec = state.completedAt 
      ? Math.max(1, ((state.completedAt - state.startedAt) / 1000)).toFixed(1)
      : "5.0";
    return {
      percent: 100,
      stageName: "Ready",
      subtext: `Completed in ${totalTimeSec}s • Indexed & Ready for AI search`,
      remainingSec: 0,
      currentStepIndex: 3,
      isCompleted: true,
      isFailed: false,
    };
  }

  const estimatedTotalSec = getEstimatedTotalSeconds(state.fileSize);
  const now = Date.now();
  const elapsedSec = Math.max(0.1, (now - state.startedAt) / 1000);

  // Phase 1: Network Upload (0% -> 25%)
  if (state.isUploading) {
    const uploadP = Math.min(100, Math.max(5, state.uploadPercent));
    const percent = Math.round(uploadP * 0.25);
    const remainingSec = Math.max(1, Math.round(estimatedTotalSec * (1 - percent / 100)));
    return {
      percent,
      stageName: "Uploading",
      subtext: `Uploading file to secure server (${uploadP}%)`,
      remainingSec,
      currentStepIndex: 0,
      isCompleted: false,
      isFailed: false,
    };
  }

  // Phase 2: Ingestion & Text Parsing / Chunking (25% -> 60%)
  if (
    state.processing_status === "UPLOADING" || 
    state.processing_status === "UPLOADED" || 
    state.processing_status === "PROCESSING" ||
    !state.processing_status
  ) {
    const parseTargetSec = estimatedTotalSec * 0.45;
    const parseRatio = Math.min(1, elapsedSec / parseTargetSec);
    const percent = Math.min(60, Math.round(25 + parseRatio * 35));
    const remainingSec = Math.max(1, Math.round(estimatedTotalSec - elapsedSec));

    return {
      percent,
      stageName: "Extracting & Chunking",
      subtext: "Extracting text passages and chunking content...",
      remainingSec,
      currentStepIndex: 1,
      isCompleted: false,
      isFailed: false,
    };
  }

  // Phase 3: AI Vector Embeddings & Qdrant Indexing (60% -> 96%)
  if (
    state.embedding_status === "PENDING" || 
    state.embedding_status === "PROCESSING" ||
    state.processing_status === "COMPLETED"
  ) {
    const parseTargetSec = estimatedTotalSec * 0.45;
    const embedElapsed = Math.max(0, elapsedSec - parseTargetSec);
    const embedTargetSec = estimatedTotalSec * 0.55;
    const embedRatio = Math.min(1, embedElapsed / embedTargetSec);
    
    let percent = Math.round(60 + embedRatio * 34);
    let remainingSec = Math.max(1, Math.round(estimatedTotalSec - elapsedSec));

    // Asymptotic smoothing if taking slightly longer
    if (elapsedSec > estimatedTotalSec) {
      const overtime = elapsedSec - estimatedTotalSec;
      percent = Math.min(96, Math.round(94 + (1 - Math.exp(-0.2 * overtime)) * 2));
      remainingSec = 1;
    }

    return {
      percent,
      stageName: "Vector Indexing",
      subtext: percent >= 92 
        ? "Finalizing Qdrant vector index..." 
        : "Generating dense AI embeddings and storing in Qdrant...",
      remainingSec,
      currentStepIndex: 2,
      isCompleted: false,
      isFailed: false,
    };
  }

  return {
    percent: 50,
    stageName: "Processing",
    subtext: "Processing document...",
    remainingSec: 2,
    currentStepIndex: 1,
    isCompleted: false,
    isFailed: false,
  };
}

/**
 * Hero Processing Card rendered above the documents table for active jobs
 */
export function DocumentProcessingCard({
  state,
  onDismiss,
}: {
  state: DocumentProcessingState;
  onDismiss?: () => void;
}) {
  // Re-render tick every 200ms for smooth fill bar motion
  const [, setTick] = useState(0);
  useEffect(() => {
    if (
      state.processing_status === "COMPLETED" && 
      state.embedding_status === "COMPLETED"
    ) {
      return;
    }
    if (state.processing_status === "FAILED" || state.embedding_status === "FAILED") {
      return;
    }

    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 200);
    return () => clearInterval(interval);
  }, [state.processing_status, state.embedding_status]);

  const { percent, stageName, subtext, remainingSec, currentStepIndex, isCompleted, isFailed } =
    computeProgressDetails(state);

  const steps = [
    { title: "Upload", icon: FileText },
    { title: "Extract & Chunk", icon: Layers },
    { title: "Vector Index", icon: Database },
    { title: "Ready", icon: Sparkles },
  ];

  return (
    <div
      className={`relative overflow-hidden rounded-xl border p-5 shadow-sm transition-all duration-300 ${
        isFailed
          ? "border-red-200 bg-red-50/40 dark:border-red-900/50 dark:bg-red-950/20"
          : isCompleted
          ? "border-emerald-200 bg-emerald-50/40 dark:border-emerald-900/40 dark:bg-emerald-950/20"
          : "border-blue-200/80 bg-gradient-to-r from-blue-50/80 via-indigo-50/40 to-purple-50/70 dark:border-blue-900/50 dark:from-blue-950/30 dark:via-zinc-900/60 dark:to-purple-950/20"
      }`}
    >
      {/* Background ambient glow */}
      {!isCompleted && !isFailed && (
        <div className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full bg-blue-400/10 blur-3xl" />
      )}

      <div className="relative z-10 flex flex-col gap-4">
        {/* Top Header: Filename, Size, Badges, Dismiss */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                isFailed
                  ? "bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400"
                  : isCompleted
                  ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400"
                  : "bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400 shadow-sm"
              }`}
            >
              {isFailed ? (
                <AlertCircle className="h-5 w-5" />
              ) : isCompleted ? (
                <CheckCircle2 className="h-5 w-5 animate-bounce" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm md:text-base">
                  {state.filename}
                </span>
                <span className="text-xs text-zinc-500 dark:text-zinc-400 font-mono">
                  ({Math.round(state.fileSize / 1024)} KB)
                </span>
              </div>
              <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-0.5 flex items-center gap-1.5">
                <span>{subtext}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isCompleted && !isFailed && (
              <Badge
                variant="outline"
                className="bg-white/70 dark:bg-zinc-800/70 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 flex items-center gap-1.5 py-1 px-2.5 font-mono text-xs shadow-xs"
              >
                <Clock className="w-3.5 h-3.5 animate-pulse text-blue-500" />
                <span>~{remainingSec}s remaining</span>
              </Badge>
            )}

            {isCompleted && (
              <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white flex items-center gap-1 shadow-xs">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Ready
              </Badge>
            )}

            {onDismiss && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                onClick={onDismiss}
                title="Dismiss"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* The Animated Fill Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-xs font-medium">
            <span
              className={
                isFailed
                  ? "text-red-600 dark:text-red-400 font-semibold"
                  : isCompleted
                  ? "text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1"
                  : "text-blue-700 dark:text-blue-300 font-medium"
              }
            >
              {stageName}
            </span>
            <span className="font-mono text-xs font-semibold text-zinc-700 dark:text-zinc-300">
              {percent}%
            </span>
          </div>

          <div className="relative h-3 w-full overflow-hidden rounded-full bg-zinc-200/80 dark:bg-zinc-800">
            <div
              className={`h-full rounded-full transition-all duration-300 ease-out relative overflow-hidden ${
                isFailed
                  ? "bg-red-500"
                  : isCompleted
                  ? "bg-gradient-to-r from-emerald-500 to-teal-400 shadow-sm"
                  : "bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500 shadow-sm"
              }`}
              style={{ width: `${percent}%` }}
            >
              {!isCompleted && !isFailed && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
              )}
            </div>
          </div>
        </div>

        {/* 4-Step Pipeline Indicators */}
        <div className="grid grid-cols-4 gap-2 pt-1">
          {steps.map((step, idx) => {
            const isStepDone = isCompleted || currentStepIndex > idx;
            const isStepCurrent = !isCompleted && currentStepIndex === idx;
            const Icon = step.icon;

            return (
              <div
                key={step.title}
                className={`flex items-center gap-1.5 text-xs transition-colors ${
                  isStepDone
                    ? "text-emerald-600 dark:text-emerald-400 font-medium"
                    : isStepCurrent
                    ? "text-blue-600 dark:text-blue-400 font-semibold"
                    : "text-zinc-400 dark:text-zinc-500"
                }`}
              >
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] ${
                    isStepDone
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                      : isStepCurrent
                      ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300 ring-2 ring-blue-400/40 animate-pulse"
                      : "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
                  }`}
                >
                  {isStepDone ? (
                    <CheckCircle2 className="h-3 w-3" />
                  ) : isStepCurrent ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>
                <span className="hidden sm:inline truncate">{step.title}</span>
              </div>
            );
          })}
        </div>

        {/* Ready Action Callout */}
        {isCompleted && (
          <div className="flex items-center justify-between pt-1 border-t border-emerald-200/60 dark:border-emerald-900/40">
            <span className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">
              Document parsed, chunked, and vector indexed into Qdrant.
            </span>
            <Link href="/chat">
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 h-8">
                <span>Start Chat</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact Inline Progress Bar rendered inside the Documents Table Status Cell
 */
export function DocumentTableStatus({
  document,
}: {
  document: {
    id: string;
    original_filename: string;
    file_size: number;
    processing_status: string;
    embedding_status: string;
    created_at: string;
    processing_error?: string;
    embedding_error?: string;
  };
}) {
  const [, setTick] = useState(0);

  const isFailed =
    document.processing_status === "FAILED" || 
    document.embedding_status === "FAILED";

  const isCompleted =
    document.processing_status === "COMPLETED" && 
    document.embedding_status === "COMPLETED";

  // Only animate if in progress
  useEffect(() => {
    if (isCompleted || isFailed) return;
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 250);
    return () => clearInterval(interval);
  }, [isCompleted, isFailed]);

  if (isFailed) {
    const errorMsg = document.processing_error || document.embedding_error || "Failed";
    return (
      <Badge variant="destructive" title={errorMsg} className="gap-1">
        <AlertCircle className="w-3 h-3" />
        Failed
      </Badge>
    );
  }

  if (isCompleted) {
    return (
      <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600 text-white gap-1">
        <CheckCircle2 className="w-3 h-3" />
        Ready
      </Badge>
    );
  }

  // Document is currently in progress (UPLOADING, PROCESSING, or INDEXING)
  const state: DocumentProcessingState = {
    id: document.id,
    filename: document.original_filename,
    fileSize: document.file_size || 100_000,
    uploadPercent: 100,
    isUploading: false,
    processing_status: document.processing_status,
    embedding_status: document.embedding_status,
    startedAt: new Date(document.created_at).getTime() || Date.now(),
  };

  const { percent, stageName, remainingSec } = computeProgressDetails(state);

  return (
    <div className="w-48 sm:w-56 space-y-1.5 py-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
          <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
          <span className="truncate max-w-[120px]">{stageName}</span>
        </span>
        <span className="font-mono text-[11px] text-zinc-500 dark:text-zinc-400">
          {percent}% • ~{remainingSec}s
        </span>
      </div>

      <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 transition-all duration-300 ease-out relative overflow-hidden"
          style={{ width: `${percent}%` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
        </div>
      </div>
    </div>
  );
}
