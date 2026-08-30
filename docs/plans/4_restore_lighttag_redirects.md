# Restore LightTag Redirects in Two Phases

Status: complete; scheduled monitoring remains
Current gate: post-migration monitoring (1 day, 1 week, and 1 month)
Last updated: 2026-08-30

- [x] P1 — Redirect infrastructure
  - [x] P1.A — CloudFormation
  - [x] P1.B — Validation tooling
  - [x] P1.C — Operations documentation
  - [x] P1.R — Sol reviews accepted
  - [x] P1.D — Production deployment verified
- [x] P2 — Search-engine migration
  - [x] P2.A — IndexNow support
  - [x] P2.B — Webmaster runbook and DNS verification
  - [x] P2.R — Sol review accepted
  - [x] P2.D — Search submissions completed

## Evidence log

- 2026-08-30: Phase 1 implementation started. Production deployment and Phase 2 remain gated.
- 2026-08-30: P1.A–P1.C implemented in `infra/lighttag-redirects/`, `Makefile`, `README.md`, and `AGENTS.md`.
- 2026-08-30: Local validator passed; 8 offline tests passed; `cfn-lint` passed; AWS `validate-template` passed in `us-east-1` with profile `local agent`; Make production targets dry-ran successfully.
- 2026-08-30: All 23 `https://talperry.com/en/posts/lighttag/<bundle>/` destinations returned canonical HTTP 200 responses.
- 2026-08-30: Deployment preflight found public delegation still points to Cloudflare (`jaime.ns.cloudflare.com`, `brianna.ns.cloudflare.com`), so Route 53 zone `Z035583412C9JWLLOM7K5` is non-authoritative and deployment remains blocked pending an owner-approved DNS migration.
- 2026-08-30: P1.R1/P1.R2 initial reviews did not grant acceptance. Remediation routed to P1.A–P1.C for DNS/certificate sequencing, fail-closed origin behavior, repeated-slash normalization, HTTP/HEAD/IP-family live checks, controlled pre-cutover validation, safer change-set/deploy targets, and documentation consistency.
- 2026-08-30: P1.R1 AWS and P1.R2 operability re-reviews accepted all remediations with no remaining actionable findings.
- 2026-08-30: Repository gate passed: `make validate` and all 69 Playwright tests succeeded.
- 2026-08-30: Created and inspected unexecuted change set `lighttag-redirects-review-20260830T055125Z` (`CREATE_COMPLETE`, `AVAILABLE`), containing the expected certificate, function, distribution, and six Route 53 alias additions.
- 2026-08-30: Real change-set output revealed that `describe-change-set` does not expose `ChangeSetType`; reopened P1.R to derive deployment waiter safety from authoritative stack status. No change set was executed.
- 2026-08-30: Final P1.R1/P1.R2 confirmation accepted stack-status-based deployment safety. AWS state remains `REVIEW_IN_PROGRESS`; the reviewed change set remains `AVAILABLE` and unexecuted with zero stack resources.
- 2026-08-30: Final verification passed: local redirect validator, 9 offline pytest tests, Ruff, strict mypy, `cfn-lint`, AWS `validate-template`, `make validate`, and 69 Playwright tests. Generated Python caches were removed; existing `.gitignore` rules cover `__pycache__/` and `*.py[cod]`.
- 2026-08-30: P1.D is intentionally not checked. Next action requires owner-approved Cloudflare/Route 53 migration following `infra/lighttag-redirects/README.md`; only then execute the reviewed change set, mirror ACM validation CNAMEs, validate the distribution before cutover, switch delegation, and run public live validation. Phase 2 remains gated on P1.D.
- 2026-08-30: Tal approved removing Cloudflare from authority. Confirmed the domain is registered with Amazon Registrar, staged the publicly visible Google Workspace MX, SPF, Mailchimp SPF, and Google verification TXT records in Route 53, and began the reviewed P1.D deployment workflow.
- 2026-08-30: Registrar nameserver operation `a7487f47-9c13-45da-b8bf-c1031a484f52` succeeded; the `.io` registry now delegates `lighttag.io` to the four Route 53 nameservers. Cloudflare is no longer authoritative.
- 2026-08-30: P1.D completed. Stack `lighttag-redirects` is `CREATE_COMPLETE` with termination protection enabled; ACM certificate is `ISSUED`; CloudFront distribution `E1W0IOXP9DCOTF` is `Deployed` with IPv6 and HTTP/2+3; apex, `www`, and guide A/AAAA aliases are present.
- 2026-08-30: Controlled live validation against `d3d8e0mrp8eep6.cloudfront.net` passed the complete redirect/410/GET/HEAD/normalization/canonical matrix. This laptop has no IPv6 route, so direct IPv6 sockets returned local `ENETUNREACH`; authoritative AAAA answers and CloudFront IPv6 enablement were verified separately. Representative direct edge probes returned exact canonical `301` responses with dropped queries and exact `410` responses for guide/unknown paths.
- 2026-08-30: P2.A/P2.B implemented. IndexNow dry-run recursively collected 95 canonical production URLs across all sitemap languages into one batch without contacting the key endpoint or IndexNow. Five offline tests, Ruff, strict mypy, `cfn-lint`, AWS template validation, and the local redirect validator passed. No search-engine submission was made; the public key endpoint remains undeployed (`404`) until the repository changes are published.
- 2026-08-30: P2.R accepted after remediation. Final implementation has 15 offline tests, exact IndexNow key/status/redirect handling, auditable batch evidence, fail-closed empty sitemap behavior, and safe 429/no-blanket-retry guidance. The unsupported CloudFormation apex-TXT import was removed; the existing verification/SPF TXT RRset remains explicitly unmanaged and protected.
- 2026-08-30: Published and verified the public IndexNow key endpoint. A deliberate guarded submission sent all 95 canonical production URLs in one batch to the global endpoint at `2026-08-30T06:51:21Z`; IndexNow returned `202 Accepted` with response evidence `sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855;bytes=0`. Do not duplicate this submission.
- 2026-08-30: Added new Google Search Console DNS verification tokens without replacing existing mail/SPF/verification TXT values. Route 53 changes `/change/C10324793A0FEYCIB90ZX` (`lighttag.io`) and `/change/C04367933VIFI7PVC7DUL` (`talperry.com`) reached `INSYNC`; both domain properties verified successfully.
- 2026-08-30: Google Search Console verified the `https://lighttag.io/`, `https://www.lighttag.io/`, and `https://talperry.com/` URL-prefix properties under Tal's account. The Tal Perry sitemap index was accepted. Change of Address validation passed and moves from both apex and `www` to `talperry.com` were confirmed with start date August 30, 2026. `guide.lighttag.io` was intentionally excluded.
- 2026-08-30: Google URL Inspection reported the representative old and restored URLs as not yet known/indexed immediately after migration. This is expected initial state and must be rechecked on the monitoring schedule.
- 2026-08-30: Bing Webmaster Tools was connected to the same Google account with read-only Search Console access. It imported `www.lighttag.io` and `talperry.com`; Bing reports the apex as already added. The imported `https://talperry.com/sitemap.xml` is `Success` with zero sitemap errors/warnings. Bing URL Inspection currently reports the representative restored page as not discovered; the global IndexNow submission is already pending and must not be duplicated.
- 2026-08-30: P2.D completed. Recheck CloudFront aggregate requests/errors after one day and one week, and review Google Search Console and Bing migration/index coverage after one week and one month. Keep the redirects for at least one year and preferably indefinitely.
