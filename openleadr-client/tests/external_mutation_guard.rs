//! Shared safety guard for destructive external-VTN integration tests.
//! Authorization is an explicit operator acknowledgement, not proof of VTN ownership.

use std::env;
use url::Url;

fn validate_target(
    mutation_opt_in: &str,
    dedicated_test_opt_in: &str,
    raw_url: &str,
    client_id: &str,
    client_secret: &str,
) -> Result<Url, String> {
    if mutation_opt_in != "I_UNDERSTAND" {
        return Err("OPENLEADR_RS_ALLOW_MUTATION must be I_UNDERSTAND".into());
    }
    if dedicated_test_opt_in != "YES" {
        return Err("OPENLEADR_RS_DEDICATED_TEST_VTN must be YES".into());
    }
    let url: Url = raw_url.parse().map_err(|e| format!("invalid VTN URL: {e}"))?;
    if url.scheme() != "https" || url.host_str().is_none() {
        return Err("mutating VTN requires HTTPS and a host".into());
    }
    if !url.username().is_empty() || url.password().is_some()
        || url.query().is_some() || url.fragment().is_some()
    {
        return Err("VTN URL cannot contain credentials, query or fragment".into());
    }
    if client_id.trim().is_empty() || client_secret.trim().is_empty() {
        return Err("explicit, nonempty VTN credentials required".into());
    }
    Ok(url)
}

pub fn authorized_mutation_url() -> Url {
    let opt_in = env::var("OPENLEADR_RS_ALLOW_MUTATION").unwrap_or_default();
    let dedicated = env::var("OPENLEADR_RS_DEDICATED_TEST_VTN").unwrap_or_default();
    let raw_url = env::var("OPENLEADR_RS_VTN_URL").unwrap_or_default();
    let client_id = env::var("OPENLEADR_RS_CLIENT_ID").unwrap_or_default();
    let client_secret = env::var("OPENLEADR_RS_CLIENT_SECRET").unwrap_or_default();
    validate_target(&opt_in, &dedicated, &raw_url, &client_id, &client_secret)
        .expect("destructive external VTN probe rejected: review opt-in, target and credentials")
}

#[cfg(test)]
mod tests {
    use super::validate_target;

    #[test]
    fn accepts_explicit_dedicated_https_target() {
        assert!(validate_target("I_UNDERSTAND", "YES", "https://vtn.example.test/",
            "client", "secret").is_ok());
    }

    #[test]
    fn rejects_missing_or_incorrect_authorization() {
        for (mutate, dedicated) in [("", "YES"), ("true", "YES"),
            ("I_UNDERSTAND", ""), ("I_UNDERSTAND", "true")] {
            assert!(validate_target(mutate, dedicated, "https://vtn.example.test/",
                "client", "secret").is_err());
        }
    }

    #[test]
    fn rejects_unsafe_targets_and_missing_credentials() {
        for url in ["http://vtn.example.test/", "https://user:pass@vtn.example.test/",
            "https://vtn.example.test/?key=1", "https://vtn.example.test/#fragment",
            "file:///tmp/vtn"] {
            assert!(validate_target("I_UNDERSTAND", "YES", url, "client", "secret").is_err());
        }
        assert!(validate_target("I_UNDERSTAND", "YES", "https://vtn.example.test/",
            "", "secret").is_err());
        assert!(validate_target("I_UNDERSTAND", "YES", "https://vtn.example.test/",
            "client", "").is_err());
    }
}
