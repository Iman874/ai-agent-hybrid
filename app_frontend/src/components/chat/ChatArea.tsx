import { useChatStore } from "@/stores/chat-store";
import { useGenerateStore } from "@/stores/generate-store";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import { useSessionStore } from "@/stores/session-store";
import { useModelStore } from "@/stores/model-store";
import { MessageBubble } from "./MessageBubble";
import { Sparkles } from "lucide-react";
import { EmptyState } from "./EmptyState";
import { ChatInput } from "./ChatInput";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { TORPreview } from "./TORPreview";
import { ChatGeneratePrompt } from "./ChatGeneratePrompt";

export function ChatArea() {
  const messages = useChatStore(s => s.messages);
  const stream = useChatStore(s => s.stream);
  const sessionState = useChatStore(s => s.sessionState);
  const toggleLiveThinkingVisible = useChatStore(s => s.toggleLiveThinkingVisible);
  const torDocument = useChatStore(s => s.torDocument);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const activeModelId = useModelStore(s => s.activeModelId);
  const scrollRef = useAutoScroll([messages.length, stream, torDocument]);
  const genIsStreaming = useGenerateStore(s => s.isStreaming);
  const genStreamSource = useGenerateStore(s => s.streamSource);
  const genStreamContent = useGenerateStore(s => s.streamingContent);

  const trimmedPartial = stream.partialContent.trimStart();
  const isJsonStreaming =
    trimmedPartial.startsWith("{") ||
    trimmedPartial.startsWith("[") ||
    trimmedPartial.includes("\"status\"") ||
    trimmedPartial.includes("\"message\"");
  const typingText = "Menyiapkan jawaban";

  const showChatStreaming =
    genStreamSource === "chat" && genIsStreaming;

  return (
    <div className="flex flex-col h-full bg-background/50">
      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 && !showChatStreaming ? (
            <div className="h-[60vh]">
              <EmptyState />
            </div>
          ) : (
            <div className="space-y-2 pb-10">
              {messages.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              
              {/* Streaming TOR langsung di TORPreview card */}
              {showChatStreaming && (
                <TORPreview
                  torDocument={{
                    content: genStreamContent || "",
                    metadata: {
                      generated_by: "",
                      generator: "",
                      mode: "",
                      word_count: genStreamContent.length,
                      generation_time_ms: 0,
                      has_assumptions: false,
                      prompt_tokens: 0,
                      completion_tokens: 0,
                    },
                  }}
                  sessionId={activeSessionId || ""}
                  isStreaming={true}
                />
              )}
              
              {torDocument && !showChatStreaming && activeSessionId && (
                <TORPreview torDocument={torDocument} sessionId={activeSessionId} />
              )}
              
              {sessionState && 
               (sessionState.status === "READY_TO_GENERATE" || 
                sessionState.status === "READY" ||
                sessionState.status === "ESCALATE_TO_GEMINI") && 
               activeSessionId && (
                <ChatGeneratePrompt 
                  sessionId={activeSessionId} 
                  status={sessionState.status}
                  completenessScore={sessionState.completeness_score}
                />
              )}
              
              {/* Streaming UI injections */}
              {stream.isThinking && (
                <ThinkingIndicator
                  text={stream.thinkingText}
                  visible={stream.thinkingVisible}
                  onToggleVisible={toggleLiveThinkingVisible}
                />
              )}
              {stream.isStreaming && !stream.isThinking && stream.partialContent && (
                isJsonStreaming ? (
                  <div className="flex gap-3 py-4">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles className="w-4 h-4 text-primary" />
                    </div>
                    <div className="max-w-[85%] sm:max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm min-w-0 box-border text-sm overflow-hidden bg-muted">
                      <div className="flex items-center gap-2">
                        <span>{typingText}</span>
                        <span className="flex gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.2s]" />
                          <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.4s]" />
                          <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-[bounce_1.4s_infinite_.6s]" />
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <MessageBubble
                    message={{
                      id: "streaming",
                      role: "assistant",
                      content: stream.partialContent,
                      status: "streaming",
                      timestamp: Date.now(),
                      modelName: activeModelId ?? undefined,
                    }}
                  />
                )
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
