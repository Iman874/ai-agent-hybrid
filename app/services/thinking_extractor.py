"""Stateful real-time thinking/reasoning extractor for LLM streaming output."""

import logging

logger = logging.getLogger("ai-agent-hybrid.thinking_extractor")

OPEN_TAGS = [
    "<think>",
    "<thinking>",
    "<reasoning>",
    "<analysis>",
    " thinking>",
    "\n thinking>",
    "\r\n thinking>",
    " thinking\n",
    "\n thinking\n",
    "\r\n thinking\n",
    " thinking\r\n",
    "\n thinking\r\n",
    "\r\n thinking\r\n",
]

CLOSE_TAGS = [
    "</think>",
    "</thinking>",
    "</reasoning>",
    "</analysis>",
    " response>",
    "\n response>",
    "\r\n response>",
    " response\n",
    "\n response\n",
    "\r\n response\n",
    " response\r\n",
    "\n response\r\n",
    "\r\n response\r\n",
]


class ThinkingExtractor:
    """Stateful extractor that separates thinking from content in real-time."""

    def __init__(self):
        self._state = "NORMAL"
        self._buffer = ""

    def feed(self, token):
        results = []
        self._buffer += token
        while True:
            if self._state == "NORMAL":
                tag_found, tag_pos = self._find_first_tag(self._buffer, OPEN_TAGS)
                if tag_found is not None:
                    before = self._buffer[:tag_pos]
                    after = self._buffer[tag_pos + len(tag_found):]
                    if before:
                        results.append(("content", before))
                    self._state = "IN_THINKING"
                    self._buffer = after
                    continue
                partial_len = self._partial_match_len(self._buffer, OPEN_TAGS)
                if partial_len > 0:
                    safe_len = len(self._buffer) - partial_len
                    if safe_len > 0:
                        results.append(("content", self._buffer[:safe_len]))
                        self._buffer = self._buffer[safe_len:]
                    break
                if self._buffer:
                    results.append(("content", self._buffer))
                    self._buffer = ""
                break
            else:
                tag_found, tag_pos = self._find_first_tag(self._buffer, CLOSE_TAGS)
                if tag_found is not None:
                    thinking = self._buffer[:tag_pos]
                    after = self._buffer[tag_pos + len(tag_found):]
                    if thinking:
                        results.append(("thinking", thinking))
                    self._state = "NORMAL"
                    self._buffer = after
                    continue
                partial_len = self._partial_match_len(self._buffer, CLOSE_TAGS)
                if partial_len > 0:
                    safe_len = len(self._buffer) - partial_len
                    if safe_len > 0:
                        results.append(("thinking", self._buffer[:safe_len]))
                        self._buffer = self._buffer[safe_len:]
                    break
                if self._buffer:
                    results.append(("thinking", self._buffer))
                    self._buffer = ""
                break
        return results

    def flush(self):
        results = []
        if self._buffer:
            if self._state == "IN_THINKING":
                results.append(("thinking", self._buffer))
            else:
                results.append(("content", self._buffer))
            self._buffer = ""
        return results

    @property
    def state(self):
        return self._state

    @staticmethod
    def _find_first_tag(text, tags):
        best_tag = None
        best_pos = -1
        for tag in tags:
            pos = text.find(tag)
            if pos != -1 and (best_tag is None or pos < best_pos):
                best_tag = tag
                best_pos = pos
        return best_tag, best_pos

    @staticmethod
    def _partial_match_len(text, tags):
        best = 0
        for tag in tags:
            for i in range(1, len(tag)):
                if text.endswith(tag[:i]) and i > best:
                    best = i
        return best
