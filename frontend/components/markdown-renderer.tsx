"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-zinc dark:prose-invert max-w-none text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm bg-white dark:bg-zinc-900/60">
                <table className="w-full text-left text-xs md:text-sm border-collapse">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return (
              <thead className="bg-zinc-100/80 dark:bg-zinc-800/70 border-b border-zinc-200 dark:border-zinc-700/80 text-zinc-900 dark:text-zinc-100 font-semibold">
                {children}
              </thead>
            );
          },
          tbody({ children }) {
            return (
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {children}
              </tbody>
            );
          },
          tr({ children }) {
            return (
              <tr className="transition-colors hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40">
                {children}
              </tr>
            );
          },
          th({ children }) {
            return (
              <th className="px-3 py-2.5 font-semibold text-zinc-900 dark:text-zinc-100 border-r border-zinc-200/60 dark:border-zinc-700/50 last:border-r-0">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3 py-2.5 text-zinc-700 dark:text-zinc-300 align-top border-r border-zinc-200/60 dark:border-zinc-800/60 last:border-r-0">
                {children}
              </td>
            );
          },
          p({ children }) {
            return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>;
          },
          ul({ children }) {
            return <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          strong({ children }) {
            return <strong className="font-semibold text-zinc-900 dark:text-zinc-100">{children}</strong>;
          },
          code({ className, children, ...props }) {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 text-xs font-mono font-medium" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <div className="overflow-x-auto my-3 rounded-lg bg-zinc-950 p-4 text-zinc-100 font-mono text-xs">
                <code className={className} {...props}>
                  {children}
                </code>
              </div>
            );
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-indigo-500/70 pl-3 my-2 italic text-zinc-600 dark:text-zinc-400">
                {children}
              </blockquote>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
