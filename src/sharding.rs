use sha2::{Digest, Sha256};

use crate::{AccountId, ShardId};

#[derive(Clone, Debug)]
pub struct ShardLayout {
    pub num_shards: u32,
}

impl ShardLayout {
    pub fn new(num_shards: u32) -> Self {
        assert!(num_shards > 0);
        Self { num_shards }
    }

    pub fn shard_for(&self, account: &AccountId) -> ShardId {
        let digest = Sha256::digest(account.as_bytes());
        let value = u32::from_be_bytes([digest[0], digest[1], digest[2], digest[3]]);
        value % self.num_shards
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn routing_is_deterministic() {
        let layout = ShardLayout::new(4);
        assert_eq!(layout.shard_for(&"alice".into()), layout.shard_for(&"alice".into()));
        assert!(layout.shard_for(&"alice".into()) < 4);
    }
}
