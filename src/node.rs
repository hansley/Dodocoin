use crate::{
    block::{Block, BlockHeader},
    chunk::{Chunk, ChunkHeader},
    crypto,
    receipt::Receipt,
    sharding::ShardLayout,
    state::{ShardState, StateError},
    transaction::SignedTransaction,
};

pub struct Node {
    pub layout: ShardLayout,
    pub shards: Vec<ShardState>,
    pub height: u64,
    pub head: crypto::Hash,
}

impl Node {
    pub fn new(num_shards: u32) -> Self {
        Self {
            layout: ShardLayout::new(num_shards),
            shards: (0..num_shards).map(|_| ShardState::default()).collect(),
            height: 0,
            head: [0; 32],
        }
    }

    pub fn execute_transfer(&mut self, signed: &SignedTransaction) -> Result<Vec<Receipt>, StateError> {
        if !signed.verify() { return Err(StateError::MissingAccount); }
        let tx = &signed.transaction;
        let from = self.layout.shard_for(&tx.sender);
        let to = self.layout.shard_for(&tx.receiver);
        self.shards[from as usize].debit(&tx.sender, tx.amount, tx.nonce)?;
        if from == to {
            self.shards[to as usize].credit(&tx.receiver, tx.amount);
            Ok(vec![])
        } else {
            Ok(vec![Receipt { from_shard: from, to_shard: to, receiver: tx.receiver.clone(), amount: tx.amount }])
        }
    }

    pub fn apply_receipt(&mut self, receipt: Receipt) {
        self.shards[receipt.to_shard as usize].credit(&receipt.receiver, receipt.amount);
    }

    pub fn produce_block(&mut self, outgoing: Vec<Receipt>) -> Block {
        self.height += 1;
        let mut chunks = Vec::new();
        for shard_id in 0..self.layout.num_shards {
            let state_root = self.shards[shard_id as usize].root();
            let shard_receipts: Vec<_> = outgoing.iter().filter(|r| r.from_shard == shard_id).cloned().collect();
            let receipt_bytes = format!("{:?}", shard_receipts).into_bytes();
            chunks.push(Chunk {
                header: ChunkHeader {
                    shard_id,
                    height: self.height,
                    prev_state_root: state_root,
                    state_root,
                    outgoing_receipts_root: crypto::hash(&receipt_bytes),
                },
                outgoing_receipts: shard_receipts,
            });
        }
        let chunks_root = Block::chunks_root(&chunks);
        let block = Block { header: BlockHeader { height: self.height, prev_hash: self.head, chunks_root }, chunks };
        self.head = block.hash();
        block
    }
}
