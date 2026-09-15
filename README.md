# DodoCoin

DodoCoin is an educational Layer-1 blockchain prototype inspired by NEAR's Nightshade sharding design.

## Status

Early testnet/protocol prototype. **Not production-ready and not intended to hold real funds.**

## Architecture goals

- One logical blockchain with state split across multiple shards
- Account-to-shard routing
- Per-shard transaction execution and chunk production
- Cross-shard receipts for transfers between accounts on different shards
- Merkle-root commitments to shard state/chunks
- Validator-oriented block/chunk model
- Deterministic local testnet simulator

This project is inspired by Nightshade concepts; it is not a fork of NEAR Protocol and does not claim protocol compatibility with NEAR.

## Planned modules

- `crypto` — hashing, signatures and addresses
- `transaction` — signed transactions, nonces and validation
- `state` — account balances and shard-local state
- `sharding` — deterministic shard assignment and routing
- `receipt` — asynchronous cross-shard messages
- `chunk` — shard execution results committed into blocks
- `block` — global block header and shard chunk commitments
- `validator` — validator identity and prototype block production
- `node` — local node/testnet orchestration

## Security

Do not use this prototype with assets of real monetary value. Production consensus, networking, slashing, data availability, stateless validation, adversarial testing, secure key management and independent security audits are outside the initial prototype scope.

## References

See NEAR Protocol's official Nightshade paper and protocol documentation for the production design that inspired this project.
