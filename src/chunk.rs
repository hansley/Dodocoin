use crate::{crypto, receipt::Receipt, ShardId};

#[derive(Clone, Debug)]
pub struct ChunkHeader {
    pub shard_id: ShardId,
    pub height: u64,
    pub prev_state_root: crypto::Hash,
    pub state_root: crypto::Hash,
    pub outgoing_receipts_root: crypto::Hash,
}

#[derive(Clone, Debug)]
pub struct Chunk {
    pub header: ChunkHeader,
    pub outgoing_receipts: Vec<Receipt>,
}

impl Chunk {
    pub fn hash(&self) -> crypto::Hash {
        let mut bytes = Vec::new();
        bytes.extend(self.header.shard_id.to_be_bytes());
        bytes.extend(self.header.height.to_be_bytes());
        bytes.extend(self.header.prev_state_root);
        bytes.extend(self.header.state_root);
        bytes.extend(self.header.outgoing_receipts_root);
        crypto::hash(&bytes)
    }
}
