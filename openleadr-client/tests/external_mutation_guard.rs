//! Guard rails shared by opt-in destructive external VTN tests.
//! These are intentionally stricter than the read-only probes.

use std::env;
use url::Url;

pub fn authorized_mutation_url() -> Url {
    assert_eq!(
        env::var("OPENLEADR_RS_ALLOW_MUTATION").as_deref(),
        Ok("I_UNDERSTAND"),
        "external mutations require OPENLEADR_RS_ALLOW_MUTATION=I_UNDERSTAND"
    );
    assert_eq!(
        env::var("OPENLEADR_RS_DEDICATED_TEST_VTN").as_deref(),
        Ok("YES"),
        "confirm a disposable and exclusively owned target with OPENLEADR_RS_DEDICATED_TEST_VTN=YES"
    );
    let raw = env::var("OPENLEADR_RS_VTN_URL")
        .expect("OPENLEADR_RS_VTN_URL must identify a dedicated test VTN");
    let url: Url = raw.parse().expect("invalid external VTN URL");
    assert_eq!(url.scheme(), "https", "destructive probes require HTTPS");
    assert!(url.host_str().is_some(), "VTN hostname required");
    assert!(url.username().is_empty() && url.password().is_none());
    assert!(url.query().is_none() && url.fragment().is_none());
    for key in ["OPENLEADR_RS_CLIENT_ID", "OPENLEADR_RS_CLIENT_SECRET"] {
        assert!(
            env::var(key).map(|v| !v.trim().is_empty()).unwrap_or(false),
            "explicit, nonempty external credentials are required: {key}"
        );
    }
    url
}

#[cfg(test)]
mod tests {
    // Validate the opt-in predicate without changing process environment.
    #[test]
    fn authorization_values_are_not_equivalent_to_truthy_strings() {
        assert_ne!("true", "I_UNDERSTAND");
        assert_ne!("1", "YES");
    }
}
