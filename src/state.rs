use std::collections::BTreeMap;
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::{AccountId, Balance};

#[derive(Clone, Debug, Default)]
pub struct Account {
    pub balance: Balance,
    pub nonce: u64,
}

#[derive(Clone, Debug, Default)]
pub struct ShardState {
    pub accounts: BTreeMap<AccountId, Account>,
}

#[derive(Debug, Error)]
pub enum StateError {
    #[error("account not found")]
    MissingAccount,
    #[error("insufficient balance")]
    InsufficientBalance,
    #[error("invalid nonce")]
    InvalidNonce,
}

impl ShardState {
    pub fn credit(&mut self, account: &AccountId, amount: Balance) {
        self.accounts.entry(account.clone()).or_default().balance += amount;
    }

    pub fn debit(&mut self, account: &AccountId, amount: Balance, nonce: u64) -> Result<(), StateError> {
        let sender = self.accounts.get_mut(account).ok_or(StateError::MissingAccount)?;
        if nonce != sender.nonce + 1 { return Err(StateError::InvalidNonce); }
        if sender.balance < amount { return Err(StateError::InsufficientBalance); }
        sender.balance -= amount;
        sender.nonce = nonce;
        Ok(())
    }

    pub fn root(&self) -> [u8; 32] {
        let mut hasher = Sha256::new();
        for (id, account) in &self.accounts {
            hasher.update(id.as_bytes());
            hasher.update(account.balance.to_be_bytes());
            hasher.update(account.nonce.to_be_bytes());
        }
        hasher.finalize().into()
    }
}
