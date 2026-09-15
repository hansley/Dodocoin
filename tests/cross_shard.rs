use dodocoin::{crypto::KeyPair, node::Node, transaction::{SignedTransaction, Transaction}};

#[test]
fn cross_shard_transfer_creates_and_applies_receipt() {
    let mut node = Node::new(4);
    let sender = "alice".to_string();
    let sender_shard = node.layout.shard_for(&sender);
    node.shards[sender_shard as usize].credit(&sender, 500);

    let receiver = (0..1000).map(|i| format!("bob-{i}"))
        .find(|a| node.layout.shard_for(a) != sender_shard).unwrap();
    let receiver_shard = node.layout.shard_for(&receiver);

    let key = KeyPair::generate();
    let tx = Transaction { sender: sender.clone(), receiver: receiver.clone(), amount: 125, nonce: 1 };
    let signed = SignedTransaction { public_key: key.public_key(), signature: key.sign(&tx.signing_bytes()), transaction: tx };
    let receipts = node.execute_transfer(&signed).unwrap();
    assert_eq!(receipts.len(), 1);
    node.apply_receipt(receipts[0].clone());

    assert_eq!(node.shards[sender_shard as usize].accounts[&sender].balance, 375);
    assert_eq!(node.shards[receiver_shard as usize].accounts[&receiver].balance, 125);
}
