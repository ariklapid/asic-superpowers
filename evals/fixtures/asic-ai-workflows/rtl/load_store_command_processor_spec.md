# Load Store Command Processor Microarchitecture

## Overview

`load_store_command_processor` accepts addressed STORE traffic from the
upstream side and drains stored entries into a WORK register for the downstream
side.

## Interfaces

- `clk_i`
- `rst_n`
- `store_valid_i`
- `store_addr_i[1:0]`
- `store_data_i[31:0]`
- `downstream_ready_i`
- `work_data_o[31:0]`
- `work_valid_o`

## Storage Organization

- `mem_q[0:3]` holds four 32-bit stored values
- `mem_valid_q[3:0]` tracks which slots contain loadable data
- `work_reg_q[31:0]` holds the next value presented downstream
- `work_valid_q` marks `work_reg_q` as valid for handshake

## Store Path

- `store_valid_i` writes `store_data_i` into `mem_q[store_addr_i]`
- `store_valid_i` sets the matching `mem_valid_q` bit
- a STORE overwrites any previous contents in the addressed slot

## Load Policy

- the load selector scans `mem_valid_q` from address 0 through address 3
- the lowest-address valid slot is the next candidate for load
- a load occurs only when at least one slot is valid and `downstream_ready_i` is high
- a successful load copies the selected slot into `work_reg_q`, sets `work_valid_q`, and clears the selected valid bit
- a newly stored empty slot becomes eligible for load on the following cycle
- if STORE and LOAD target the same slot in one cycle, LOAD consumes the pre-cycle contents and STORE leaves the new data resident in that slot

## Reset Behavior

- reset clears `mem_q`, `mem_valid_q`, `work_reg_q`, and `work_valid_q`

## PPA Notes

- keep the block in one synchronous domain with register-based storage only
- prefer deterministic fixed-priority load selection over wider arbitration logic
- keep idle switching low by holding state when no store or load event occurs
