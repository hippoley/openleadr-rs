// Transplant draft for kubernetes-sigs/gateway-api#4303.
// NOT a normative conformance test until the losing Route condition/reason is settled upstream.
// Target path upstream: conformance/tests/httproute-exact-conflict.go
package adoption

const GatewayAPI4303Draft = `
var HTTPRouteExactConflict = confsuite.ConformanceTest{
    ShortName:   "HTTPRouteExactConflict",
    Description: "Two conflict-equivalent HTTPRoutes expose the deterministic loser in status and route traffic only to the winner",
    Features: []features.FeatureName{
        features.SupportGateway,
        features.SupportHTTPRoute,
    },
    Manifests: []string{"tests/httproute-exact-conflict.yaml"},
    Test: func(t *testing.T, suite *confsuite.ConformanceTestSuite) {
        ns := confsuite.InfrastructureNamespace
        gwNN := types.NamespacedName{Name: "same-namespace", Namespace: ns}
        winnerNN := types.NamespacedName{Name: "exact-conflict-a", Namespace: ns}
        loserNN := types.NamespacedName{Name: "exact-conflict-b", Namespace: ns}

        // Wait for current-generation status on both Routes before interpreting conditions.
        kubernetes.HTTPRouteMustHaveLatestConditions(t, suite.Client, suite.TimeoutConfig, winnerNN)
        kubernetes.HTTPRouteMustHaveLatestConditions(t, suite.Client, suite.TimeoutConfig, loserNN)

        gwAddr := kubernetes.GatewayAndHTTPRoutesMustBeAccepted(
            t, suite.Client, suite.TimeoutConfig, suite.ControllerName,
            kubernetes.NewGatewayRef(gwNN), winnerNN,
        )

        // BLOCKED by #4303: replace this comment with the normative losing Route
        // condition/reason once the API decision is made. Do not guess Accepted=False
        // vs Programmed=False or a Conflicted reason locally.

        http.MakeRequestAndExpectEventuallyConsistentResponse(
            t, suite.RoundTripper, suite.TimeoutConfig, gwAddr,
            http.ExpectedResponse{
                Request: http.Request{Path: "/exact-conflict"},
                Backend: confsuite.InfraBackendServiceNameV1,
                Namespace: ns,
            },
        )

        // A final upstream version should delete the winner and verify that the former
        // loser becomes effective, proving it was suppressed by precedence rather than invalid.
        _ = loserNN
    },
}
`
