use dodocoin::{crypto::KeyPair, node::Node, transaction::{SignedTransaction, Transaction}, DEFAULT_SHARDS};

fn main() {
    let mut node = Node::new(DEFAULT_SHARDS);
    let alice = "alice".to_string();
    let bob = "bob".to_string();
    let alice_shard = node.layout.shard_for(&alice);
    node.shards[alice_shard as usize].credit(&alice, 1_000_000);

    let key = KeyPair::generate();
    let tx = Transaction { sender: alice, receiver: bob, amount: 100, nonce: 1 };
    let signed = SignedTransaction {
        public_key: key.public_key(),
        signature: key.sign(&tx.signing_bytes()),
        transaction: tx,
    };

    let receipts = node.execute_transfer(&signed).expect("valid transfer");
    let block = node.produce_block(receipts.clone());
    for receipt in receipts { node.apply_receipt(receipt); }

    println!("DodoCoin produced block {}: {}", block.header.height, hex::encode(block.hash()));
}
