import { useChatStore } from "@/stores/chat-store";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import { useSessionStore } from "@/stores/session-store";
import { MessageBubble } from "./MessageBubble";
import { EmptyState } from "./EmptyState";
import { ChatInput } from "./ChatInput";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { TORPreview } from "./TORPreview";

export function ChatArea() {
  const messages = useChatStore(s => s.messages);
  const stream = useChatStore(s => s.stream);
  const torDocument = useChatStore(s => s.torDocument);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const scrollRef = useAutoScroll([messages.length, stream, torDocument]);

  return (
    <div className="flex flex-col h-full bg-background/50">
      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <div className="h-[60vh]">
              <EmptyState />
            </div>
          ) : (
            <div className="space-y-2 pb-10">
              {messages.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              
              {torDocument && activeSessionId && (
                <TORPreview torDocument={torDocument} sessionId={activeSessionId} />
              )}
              
              {/* Streaming UI injections */}
              {stream.isThinking && <ThinkingIndicator text={stream.thinkingText} />}
              {stream.isStreaming && !stream.isThinking && stream.partialContent && (
                <MessageBubble
                  message={{
                    id: "streaming",
                    role: "assistant",
                    content: stream.partialContent,
                    status: "streaming",
                    timestamp: Date.now(),
                  }}
                />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="pb-2 relative bg-gradient-to-t from-background via-background to-transparent pt-6">
        <ChatInput />
      </div>
    </div>
  );
}
