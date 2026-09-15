use serde::{Deserialize, Serialize};

use crate::{crypto, AccountId, Balance};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Transaction {
    pub sender: AccountId,
    pub receiver: AccountId,
    pub amount: Balance,
    pub nonce: u64,
}

impl Transaction {
    pub fn signing_bytes(&self) -> Vec<u8> {
        serde_json::to_vec(self).expect("transaction serialization")
    }
}

#[derive(Clone, Debug)]
pub struct SignedTransaction {
    pub transaction: Transaction,
    pub public_key: [u8; 32],
    pub signature: [u8; 64],
}

impl SignedTransaction {
    pub fn verify(&self) -> bool {
        crypto::verify(&self.public_key, &self.transaction.signing_bytes(), &self.signature)
    }
}
