"""Offline test: proves history accumulates and errors don't corrupt it.
No API key or network needed."""
from study_buddy import SYSTEM_PROMPT, chat_turn

seen = []
def fake_ask(messages):
    seen.append(len(messages))
    return f"reply #{len(seen)}"

msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
for q in ["What is photosynthesis?", "Where does it happen?", "Why is it green?"]:
    chat_turn(fake_ask, msgs, q)

assert seen == [2, 4, 6], seen          # each call carries all previous turns
assert [m["role"] for m in msgs] == ["system"] + ["user", "assistant"] * 3

def failing_ask(messages):
    raise ConnectionError("network down")

before = len(msgs)
assert chat_turn(failing_ask, msgs, "hello?") is None
assert len(msgs) == before              # failed turn rolled back
print("All memory and error-handling tests passed.")
