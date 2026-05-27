# Status FIFO Intent

- The block is a small synchronous FIFO with occupancy status.
- Writes are ignored and `overflow` pulses when the FIFO is already full.
- Reads are ignored and `underflow` pulses when the FIFO is empty.
- `level` tracks occupancy.
- Reset clears storage state and status outputs.
