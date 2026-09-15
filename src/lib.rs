pub mod block;
pub mod chunk;
pub mod crypto;
pub mod node;
pub mod receipt;
pub mod sharding;
pub mod state;
pub mod transaction;

pub type AccountId = String;
pub type Balance = u128;
pub type ShardId = u32;

pub const DEFAULT_SHARDS: u32 = 4;
