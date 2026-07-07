# Task 12 — Update Chat Components

## Deskripsi

Integrasi AgentIndicator ke dalam komponen chat yang existing.

---

## File yang Diubah

### `app_frontend/src/components/chat/ChatArea.tsx`

- Import `AgentIndicator` + `useChatStore`
- Render `AgentIndicator` di atas streaming text kalo `activeAgent` terisi
- Integrasi dengan component layout yang ada

### `app_frontend/src/components/chat/MessageBubble.tsx` (optional)

- Kalo perlu nunjukkin agent info di setiap message bubble, tambah label kecil

### `app_frontend/src/components/chat/StreamingText.tsx`

- Integrasi agent indicator di atas animated text

---

## Layout Changes (ChatArea.tsx)

```tsx
<div className="chat-area">
  <MessagesList messages={messages} />
  
  {/* NEW: Agent indicator during streaming */}
  {activeAgent && (
    <AgentIndicator
      activeAgent={activeAgent}
      agentAction={agentAction}
      isStreaming={isStreaming}
    />
  )}
  
  {/* Streaming content */}
  {partialContent && (
    <div className="streaming-content">
      <StreamingText content={partialContent} />
    </div>
  )}
  
  <ChatInput onSend={sendMessage} />
</div>
```

---

## Acceptance Criteria

- [ ] AgentIndicator muncul di ChatArea pas streaming
- [ ] Posisinya tepat di atas streaming text
- [ ] Tidak merusak layout yang ada
- [ ] Kompatibel dengan light/dark mode

---

## Dependencies

- Task 10 (AgentIndicator component)
- Task 11 (Chat store updates)

---

## Estimasi

**Low** (~1 jam)
