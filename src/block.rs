use crate::{chunk::Chunk, crypto};

#[derive(Clone, Debug)]
pub struct BlockHeader {
    pub height: u64,
    pub prev_hash: crypto::Hash,
    pub chunks_root: crypto::Hash,
}

#[derive(Clone, Debug)]
pub struct Block {
    pub header: BlockHeader,
    pub chunks: Vec<Chunk>,
}

impl Block {
    pub fn hash(&self) -> crypto::Hash {
        let mut bytes = Vec::new();
        bytes.extend(self.header.height.to_be_bytes());
        bytes.extend(self.header.prev_hash);
        bytes.extend(self.header.chunks_root);
        crypto::hash(&bytes)
    }

    pub fn chunks_root(chunks: &[Chunk]) -> crypto::Hash {
        let mut bytes = Vec::new();
        for chunk in chunks { bytes.extend(chunk.hash()); }
        crypto::hash(&bytes)
    }
}
