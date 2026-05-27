# Streaming Buffer Intent

- The block buffers one item between an input ready/valid interface and an output
  ready/valid interface.
- Backpressure is applied when the single entry is full.
- Reset clears the buffer state.
- The design intent does not define whether same-cycle pass-through is required.
