use crate::{AccountId, Balance, ShardId};

#[derive(Clone, Debug)]
pub struct Receipt {
    pub from_shard: ShardId,
    pub to_shard: ShardId,
    pub receiver: AccountId,
    pub amount: Balance,
}
