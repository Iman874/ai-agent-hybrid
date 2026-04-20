import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { memo } from "react";

export const MarkdownRenderer = memo(function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none text-sm break-words leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-semibold mt-4 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="font-semibold mt-3 mb-2">{children}</h3>,
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const isInline = !match && !className?.includes('language-');
            return isInline ? (
              <code className="bg-muted px-1.5 py-0.5 rounded text-[0.8em] font-mono" {...props}>{children}</code>
            ) : (
              <div className="rounded-md bg-[#1e1e1e] overflow-hidden my-3">
                <div className="flex items-center justify-between px-3 py-1.5 bg-[#2d2d2d] text-xs text-zinc-300">
                  <span>{match?.[1] || 'code'}</span>
                </div>
                <pre className="p-3 overflow-x-auto text-[0.85em] leading-snug">
                  <code className={className} {...props}>{children}</code>
                </pre>
              </div>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/50 pl-4 py-1 italic text-muted-foreground my-3 bg-muted/20 rounded-r-lg">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4 w-full">
              <table className="w-full border-collapse border border-border text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted text-muted-foreground text-left">{children}</thead>,
          tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
          tr: ({ children }) => <tr className="hover:bg-muted/50 transition-colors">{children}</tr>,
          th: ({ children }) => <th className="border border-border px-4 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border border-border px-4 py-2 align-top">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
