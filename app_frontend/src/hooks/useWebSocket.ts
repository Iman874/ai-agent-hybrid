import { useEffect, useRef } from "react";
import { WebSocketManager } from "@/ws/socket";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";

export function useWebSocket() {
  const wsRef = useRef<WebSocketManager | null>(null);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  
  const appendToken = useChatStore(s => s.appendToken);
  const setThinking = useChatStore(s => s.setThinking);
  const appendThinkingToken = useChatStore(s => s.appendThinkingToken);
  const finalizeStream = useChatStore(s => s.finalizeStream);
  const setError = useChatStore(s => s.setError);
  const setWSManager = useChatStore(s => s.setWSManager);

  useEffect(() => {
    const ws = new WebSocketManager("/ws/chat");
    
    ws.onToken = appendToken;
    ws.onThinkingStart = () => setThinking(true);
    ws.onThinkingToken = appendThinkingToken;
    ws.onThinkingEnd = () => setThinking(false);
    ws.onDone = finalizeStream;
    ws.onError = (err) => {
      const messages = useChatStore.getState().messages;
      const lastAssistant = [...messages].reverse().find((m: any) => m.role === "assistant");
      // Jika masih ada sending/streaming request
      if (lastAssistant && (lastAssistant.status === "sending" || lastAssistant.status === "streaming")) {
          setError(lastAssistant.id, err);
      }
    };
    
    ws.connect(activeSessionId ?? undefined);
    wsRef.current = ws;
    setWSManager(ws);

    return () => {
      ws.disconnect();
      setWSManager(null);
    };
  }, [activeSessionId, appendToken, setThinking, appendThinkingToken, finalizeStream, setError, setWSManager]);

  return wsRef;
}
