import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";

export function StreamingText({ text }: { text: string }) {
  // Append block character to simulate cursor blinking at the end of streaming text
  return <MarkdownRenderer content={text + " ▋"} />;
}
