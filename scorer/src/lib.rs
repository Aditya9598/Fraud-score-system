use serde::{Deserialize, Serialize};

pub const CONTRACT_VERSION: &str = "1.0";

#[derive(Debug, Deserialize, PartialEq)]
pub struct TransactionInput {
    pub contract_version: String,
    pub transaction_id: String,
    pub user_id: u64,
    pub amount: f64,
    #[serde(rename = "type")]
    pub tx_type: String,
    pub merchant: String,
}

#[derive(Debug, Serialize, PartialEq)]
pub struct ScoreOutput {
    pub contract_version: String,
    pub transaction_id: String,
    pub risk_score: u32,
    pub risk_level: String,
    pub reasons: Vec<String>,
}

pub fn score_transaction(input: &TransactionInput) -> Result<ScoreOutput, String> {
    if input.contract_version != CONTRACT_VERSION {
        return Err(format!(
            "unsupported contract_version: {}",
            input.contract_version
        ));
    }

    let mut score: u32 = 0;
    let mut reasons: Vec<String> = Vec::new();

    if input.amount >= 1000.0 {
        score += 40;
        reasons.push("high_amount".to_string());
    } else if input.amount >= 500.0 {
        score += 20;
        reasons.push("medium_amount".to_string());
    }

    if input.tx_type == "debit" && input.amount >= 300.0 {
        score += 25;
        reasons.push("large_debit".to_string());
    }

    if score > 100 {
        score = 100;
    }

    let risk_level = if score >= 70 {
        "high"
    } else if score >= 40 {
        "medium"
    } else {
        "low"
    };

    Ok(ScoreOutput {
        contract_version: CONTRACT_VERSION.to_string(),
        transaction_id: input.transaction_id.clone(),
        risk_score: score,
        risk_level: risk_level.to_string(),
        reasons,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_tx(amount: f64, tx_type: &str) -> TransactionInput {
        TransactionInput {
            contract_version: "1.0".to_string(),
            transaction_id: "tx-1".to_string(),
            user_id: 1,
            amount,
            tx_type: tx_type.to_string(),
            merchant: "acme".to_string(),
        }
    }

    #[test]
    fn scores_high_amount_debit() {
        let result = score_transaction(&sample_tx(1000.0, "debit")).unwrap();
        assert_eq!(result.risk_score, 65);
        assert_eq!(result.risk_level, "medium");
    }

    #[test]
    fn scores_small_credit_low() {
        let result = score_transaction(&sample_tx(100.0, "credit")).unwrap();
        assert_eq!(result.risk_score, 0);
        assert_eq!(result.risk_level, "low");
    }

    #[test]
    fn rejects_wrong_contract_version() {
        let mut tx = sample_tx(100.0, "credit");
        tx.contract_version = "2.0".to_string();
        assert!(score_transaction(&tx).is_err());
    }
}
