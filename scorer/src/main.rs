use scorer::{score_transaction, TransactionInput};
use std::io::{self, Read};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 || args[1] != "score" {
        eprintln!("Usage: scorer score   (reads JSON from stdin)");
        std::process::exit(1);
    }

    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .expect("failed to read stdin");

    let tx: TransactionInput = match serde_json::from_str(&input) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("invalid json: {e}");
            std::process::exit(1);
        }
    };

    match score_transaction(&tx) {
        Ok(score) => {
            println!("{}", serde_json::to_string(&score).unwrap());
        }
        Err(e) => {
            eprintln!("{e}");
            std::process::exit(1);
        }
    }
}
