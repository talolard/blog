# LightTag redirect operations

This runbook is the operating record for the legacy LightTag URL redirects. The
redirect map is intentionally small and explicit: an article URL that is not in
the map must not silently fall through to a new article or the site home page.
Unknown paths return `410 Gone`.

The imported bundles' `[original_publication]` front matter is authoritative for
the 23 provenance pairs. The typed validator derives expected pairs from that
front matter and checks the CloudFormation map. This human-readable table is a
reviewer-maintained copy; review it against front matter and the template. Keep
all three representations in sync. The production stack is deliberately
retained for at least one year and preferably indefinitely: old links,
bookmarks, citations, and crawlers can
arrive long after the migration.

## Ownership and AWS context

- AWS account and credentials: Tal's `local agent` profile. Never put
  credentials, certificate ARNs, or DNS secrets in this repository.
- Region: `us-east-1`. CloudFront is global, and ACM certificates used by
  CloudFront must be issued in `us-east-1`.
- Suggested stack name: `lighttag-redirects`.
- Operational owner: Tal Perry. The owner approves DNS delegation, production
  changes, and rollback. The repository owner reviews map and template changes.
- The stack is a CloudFront distribution with an ACM certificate and a
  viewer-request CloudFront Function. The function owns the exact allowlist,
  emits permanent redirects, and emits `410 Gone` for unknown requests before
  the configured `talperry.com` fallback origin can be used. Keep the map and
  response behavior in the template, not in an ad-hoc console edit.

The expected steady-state cost is low but not zero: CloudFront requests and
data transfer are usage based, CloudFront Function invocations are usage based,
ACM certificates are free, and a Route53 hosted zone (if used) is charged per
month. DNS queries can add usage charges. This design has no access-log
pipeline, WAF, or per-path telemetry. Confirm current AWS prices before
approving a change; the important operational property is that there is no
always-on compute or database.
Tag or otherwise record the stack as `Project=lighttag-redirects`,
`Owner=tal-perry`, and `ManagedBy=cloudformation` where the template supports
it. Do not delete the stack merely to reduce a small recurring cost.

## DNS state and completed migration

Do this read-only check before creating a change set or changing DNS:

```sh
dig +short NS lighttag.io @1.1.1.1
dig +trace NS lighttag.io
aws route53 get-hosted-zone --id Z035583412C9JWLLOM7K5 --profile 'local agent'
aws route53 list-resource-record-sets --hosted-zone-id Z035583412C9JWLLOM7K5 \
  --profile 'local agent' --region us-east-1
```

Route53 is now authoritative for `lighttag.io`. The registrar delegates to
`ns-1214.awsdns-23.org`, `ns-370.awsdns-46.com`, `ns-1909.awsdns-46.co.uk`, and
`ns-878.awsdns-45.net`; hosted zone `Z035583412C9JWLLOM7K5` is the production
zone. The `lighttag-redirects` stack is `CREATE_COMPLETE` with termination
protection enabled, certificate `ISSUED`, and CloudFront distribution
`E1W0IOXP9DCOTF` deployed at `d3d8e0mrp8eep6.cloudfront.net`.

The deployed zone includes the apex and `www`/`guide` A and AAAA aliases, the
Google Workspace MX set (including the verification MX), ACM validation CNAMEs,
and one apex TXT RRset containing `Authenticate Domain`, an existing
`google-site-verification` token, and the SPF record. Preserve this complete
RRset: do not create a second same-name TXT record or replace it with an
incomplete UPSERT. The existing apex token is the preferred verification path;
no token is committed to this repository.

Run this read-only preflight before any future change set or DNS operation and
record the output with the change ticket:

### Historical Cloudflare-to-Route53 migration record

The following sequence records the completed migration and remains the rollback
runbook. Cloudflare was authoritative during certificate issuance and stack
bring-up; it is no longer authoritative. Never repeat the registrar change as
part of an ordinary redirect update, and retain the old nameservers and export
for rollback.

1. Exported the Cloudflare DNS record set, TTLs, and registrar settings;
   identify mail, verification, and existing web records. Lower relevant TTLs
   before the maintenance window.
2. Created and inspected, but did not execute, a `CREATE` change set while
   Cloudflare remained authoritative. Checked the distribution aliases,
   certificate, Route53 records, fallback origin, and exact 23 mappings:

   ```sh
   export LIGHTTAG_REDIRECT_CHANGE_SET=lighttag-redirects-first-$(date +%Y%m%d%H%M%S)
   export LIGHTTAG_REDIRECT_CHANGE_SET_TYPE=CREATE
   make lighttag-redirect-change-set
   aws cloudformation describe-change-set \
     --stack-name lighttag-redirects \
     --change-set-name "$LIGHTTAG_REDIRECT_CHANGE_SET" \
     --region us-east-1 --profile 'local agent'
   ```

3. Executed the reviewed change set. CloudFormation requested the ACM
   certificate and creates its DNS-validation records in the requested
   Route53 zone, then waits while the certificate is pending. Keep this
   process running in one terminal:

   ```sh
   make lighttag-redirect-deploy > /tmp/lighttag-redirect-deploy.log 2>&1 &
   deploy_pid=$!
   ```

4. In a second terminal, discovered the exact certificate ARN and validation
   CNAMEs. Poll until the certificate ARN exists and all three domain-validation
   records have complete name/type/value fields; only then copy those exact
   records to Cloudflare, then the authoritative provider. Do not invent
   values or replace them with a broad wildcard:

   ```sh
   set -eu
   cert_arn=''
   for attempt in $(seq 1 60); do
     cert_arn=$(aws cloudformation describe-stack-resource \
       --stack-name lighttag-redirects --logical-resource-id LightTagCertificate \
       --query 'StackResourceDetail.PhysicalResourceId' --output text \
       --region us-east-1 --profile 'local agent' 2>/dev/null || true)
     if test -n "$cert_arn" && test "$cert_arn" != None; then break; fi
     sleep 10
   done
   test -n "$cert_arn" && test "$cert_arn" != None
   record_count=0
   for attempt in $(seq 1 60); do
     record_count=$(aws acm describe-certificate --certificate-arn "$cert_arn" \
       --query 'length(Certificate.DomainValidationOptions[?ResourceRecord.Name!=null && ResourceRecord.Type!=null && ResourceRecord.Value!=null])' \
       --output text --region us-east-1 --profile 'local agent' 2>/dev/null || true)
     if test "$record_count" = 3; then break; fi
     sleep 10
   done
   test "$record_count" = 3
   aws acm describe-certificate --certificate-arn "$cert_arn" \
     --query 'Certificate.DomainValidationOptions[].ResourceRecord' \
     --output table --region us-east-1 --profile 'local agent'
   aws route53 list-resource-record-sets \
     --hosted-zone-id Z035583412C9JWLLOM7K5 --region us-east-1 \
     --profile 'local agent'
   ```

5. Waited for ACM, CloudFormation, and CloudFront explicitly. The Make deploy
   target performs the stack and distribution waits and enables termination
   protection; these commands are useful evidence and diagnosis:

   ```sh
   aws acm wait certificate-validated --certificate-arn "$cert_arn" \
     --region us-east-1 --profile 'local agent'
   aws cloudformation wait stack-create-complete --stack-name lighttag-redirects \
     --region us-east-1 --profile 'local agent'
   distribution_id=$(aws cloudformation describe-stack-resource \
     --stack-name lighttag-redirects --logical-resource-id LightTagDistribution \
     --query 'StackResourceDetail.PhysicalResourceId' --output text \
     --region us-east-1 --profile 'local agent')
   distribution_domain=$(aws cloudformation describe-stacks \
     --stack-name lighttag-redirects \
     --query "Stacks[0].Outputs[?OutputKey=='DistributionDomainName'].OutputValue | [0]" \
     --output text --region us-east-1 --profile 'local agent')
   aws cloudfront wait distribution-deployed --id "$distribution_id" \
     --region us-east-1 --profile 'local agent'
   ```

6. Confirmed termination protection and ran the live validator against the
   distribution hostname as a controlled connect target. The validator keeps
   each logical legacy hostname in the URL, `Host`, and TLS SNI while sending
   the TCP connection to the distribution target:

   ```sh
   aws cloudformation describe-stacks --stack-name lighttag-redirects \
     --query 'Stacks[0].EnableTerminationProtection' --output text \
     --region us-east-1 --profile 'local agent'
   distribution_domain=$(aws cloudformation describe-stacks \
     --stack-name lighttag-redirects \
     --query "Stacks[0].Outputs[?OutputKey=='DistributionDomainName'].OutputValue | [0]" \
     --output text --region us-east-1 --profile 'local agent')
   make lighttag-redirect-live-test \
     LIGHTTAG_REDIRECT_LIVE_ARGS="--live --connect-host $distribution_domain"
   ```

   Return to terminal 1 and run `wait "$deploy_pid"` so the background
   deployment's exit status is observed.

7. Fully populated and audited the Route53 zone (including mail and verification
   records) against the saved Cloudflare export. Only after ACM is `ISSUED`,
   the stack is complete, the distribution is `Deployed`, termination
   protection is enabled, and all records are present should the registrar be
   changed to the four nameservers returned by `get-hosted-zone`. Keep the
   Cloudflare export and old nameservers for rollback. Wait for delegation and
   resolver caches to converge, verify from multiple resolvers, and then raise
   TTLs after a stable observation window.

Rollback remains restoration of the prior Cloudflare nameserver delegation (and the
saved records) at the registrar, not to delete the hosted zone or distribution.
Keep the distribution and certificate available while DNS recovers; verify
both the old and new authoritative answers before declaring rollback complete.
If a future migration away from Route53 is approved, revise the stack's DNS
scope first and do not leave an alias that cannot be authoritative.

## Google Search Console DNS verification

The authoritative apex TXT RRset already contains a Google Search Console
verification value. Use that existing value to verify the `lighttag.io` Domain
property and the `www.lighttag.io` URL-prefix property in the same Google
account; do not add a second `lighttag.io TXT` record. Keep `Authenticate
Domain` and the complete SPF value in the RRset because they support existing
mail/domain services. Verify `talperry.com` in that same account using the
verification method offered for that property. Google explains that Domain
properties require DNS verification and that verification tokens should not be
overwritten: [Search Console ownership verification](https://support.google.com/webmasters/answer/9008080)
and [property types](https://support.google.com/webmasters/answer/34592).

This is an explicit exception to the original optional-parameter idea:
`AWS::Route53::RecordSet` is not supported by CloudFormation resource import,
and the redirect stack must not attempt to own this shared apex RRset. There is
no GSC parameter, condition, or TXT resource in the template. No verification
token belongs in this repository.

The existing apex token remains unmanaged in the authoritative Route53 zone
alongside `Authenticate Domain` and SPF. Verify it read-only before using it;
do not create a second same-name TXT record:

```sh
aws route53 list-resource-record-sets \
  --hosted-zone-id Z035583412C9JWLLOM7K5 \
  --query 'ResourceRecordSets[?Name==`lighttag.io.` && Type==`TXT`]' \
  --profile 'local agent' --region us-east-1
```

If a future token must be added or rotated, obtain owner approval and update
the authoritative Route53 RRset directly. First export the current complete
RRset, retain every existing value (including mail/domain-service values and
any other verification tokens), then prepare a full `UPSERT`; an UPSERT that
contains only the new Google value would delete the other values:

```sh
# Build this file locally from the just-read authoritative RRset; do not
# commit it or put real verification tokens in shell history/repository files.
# Include every current value, plus the approved new value if appropriate.
aws route53 change-resource-record-sets \
  --hosted-zone-id Z035583412C9JWLLOM7K5 \
  --change-batch file:///path/to/owner-approved-full-apex-txt-upsert.json \
  --region us-east-1 --profile 'local agent'
```

After the approved update, verify the authoritative result with
`list-resource-record-sets` and public DNS. This direct Route53 operation is
never part of the CloudFormation redirect stack, tests, CI, or automated search
submission. If the RRset contains extra values or multiple active Google
tokens, preserve them unless the owner explicitly authorizes retirement.

## Canonical redirect map (23 entries)

The left column is the exact historical `original_publication.path` from the
corresponding bundle. The right column is the current Hugo bundle destination.
The typo in the historical `imporvement` path is preserved as the source key;
it redirects to the corrected `improvement` bundle. Query strings are
intentionally dropped: each `Location` is exactly the destination shown in the
table. Both `GET` and `HEAD` must behave the same.

The corrected spelling `/blog/active-learning-optimization-is-not-improvement/`
is an explicit compatibility alias in the function, outside the 23 provenance
pairs. It must remain tested but must not be added to front matter, the table
count, or the 23-entry source allowlist.

| # | Historical LightTag path | Current bundle destination |
|---:|---|---|
| 1 | `/blog/active-learning-manager/` | `/en/posts/lighttag/active-learning-manager/` |
| 2 | `/blog/active-learning-optimization-is-not-imporvement/` | `/en/posts/lighttag/active-learning-optimization-is-not-improvement/` |
| 3 | `/blog/character-level-NLP/` | `/en/posts/lighttag/character-level-nlp/` |
| 4 | `/blog/sequence-labeling-with-transformers/example` | `/en/posts/lighttag/code-to-align-annotations-with-huggingface-tokenizers/` |
| 5 | `/blog/complement-objective-training-with-pytorch-lightning/` | `/en/posts/lighttag/complement-objective-training-with-pytorch-lightning/` |
| 6 | `/blog/context-is-king/` | `/en/posts/lighttag/context-is-king/` |
| 7 | `/blog/database-multi-tenancy/` | `/en/posts/lighttag/database-multi-tenancy/` |
| 8 | `/blog/efficiently-label-data-for-nlp/` | `/en/posts/lighttag/efficiently-label-data-for-nlp/` |
| 9 | `/blog/embrace-the-noise/` | `/en/posts/lighttag/embrace-the-noise/` |
| 10 | `/blog/fast-nlp-pretraining-with-vampire/` | `/en/posts/lighttag/fast-nlp-pretraining-with-vampire/` |
| 11 | `/how-to-label-data/` | `/en/posts/lighttag/how-to-label-data/` |
| 12 | `/blog/indexeddb-for-nlp/` | `/en/posts/lighttag/indexeddb-for-nlp/` |
| 13 | `/blog/krippendorffs-alpha/` | `/en/posts/lighttag/krippendorffs-alpha/` |
| 14 | `/blog/lighttag-acquired-by-primer/` | `/en/posts/lighttag/lighttag-acquired-by-primer/` |
| 15 | `/blog/postmortem-docker-swarm-wrong-tag/` | `/en/posts/lighttag/postmortem-docker-swarm-wrong-tag/` |
| 16 | `/blog/psql-range-aggregation-for-nlp/` | `/en/posts/lighttag/psql-range-aggregation-for-nlp/` |
| 17 | `/blog/react-dc-js/` | `/en/posts/lighttag/react-dc-js/` |
| 18 | `/blog/sequence-labeling-with-transformers/` | `/en/posts/lighttag/sequence-labeling-with-transformers/` |
| 19 | `/blog/snorql/` | `/en/posts/lighttag/snorql/` |
| 20 | `/blog/spacy-vs-stanford/` | `/en/posts/lighttag/spacy-vs-stanford/` |
| 21 | `/blog/tensorflow-estimator-api/` | `/en/posts/lighttag/tensorflow-estimator-api/` |
| 22 | `/blog/unicode-surrogate-pairs/` | `/en/posts/lighttag/unicode-surrogate-pairs/` |
| 23 | `/blog/when-to-use-machine-in-the-loop/` | `/en/posts/lighttag/when-to-use-machine-in-the-loop/` |

The destination origin is fixed at `https://talperry.com/`. A controlled live
connection may override only the network connect target; it must preserve the
logical legacy hostname in the request and TLS SNI. Never put a LightTag or
`guide.lighttag.io` URL in a destination.

The article table is a reviewer-maintained, human-readable copy of the
23-entry migration contract. Review it against the authoritative front matter
and the template. If the template also
keeps an explicit archive-root convenience route (`/` or `/guide/`), treat it
as a separately reviewed alias; every other unmapped path and host must remain
`410 Gone`.

## Local validation and review

Run these checks from the repository root. They are read-only and do not submit
anything to a search engine or mutate AWS:

```sh
make lighttag-redirect-test
make lighttag-redirect-validate
make lighttag-redirect-cfn-check
AWS_PROFILE='local agent' AWS_DEFAULT_REGION=us-east-1 \
  aws cloudformation validate-template \
  --template-body file://infra/lighttag-redirects/template.yaml
```

The local validator must verify all 23 rows against the `path` fields in
`content/posts/lighttag/**/index.md`, ensure every destination bundle exists,
reject duplicates, reject non-LightTag source hosts, and reject a catch-all
redirect. The Makefile runs `cfn-lint` through `uvx`, so no global install is
required. A reviewer should inspect the rendered change set even when all local
validators pass.

## Change set, deploy, rollback, and live test

All AWS commands use `us-east-1` and the profile with a space in its name. Set
the variables explicitly for a production operation; the Makefile defaults are
deliberately conservative. A change set must be created and reviewed before
execution.

```sh
export AWS_PROFILE='local agent'
export AWS_REGION=us-east-1
export LIGHTTAG_REDIRECT_STACK=lighttag-redirects
export LIGHTTAG_REDIRECT_CHANGE_SET=lighttag-redirects-$(date +%Y%m%d%H%M%S)
# Use CREATE for the first stack and UPDATE for an existing stack.
export LIGHTTAG_REDIRECT_CHANGE_SET_TYPE=UPDATE

make lighttag-redirect-change-set
aws cloudformation describe-change-set \
  --stack-name "$LIGHTTAG_REDIRECT_STACK" \
  --change-set-name "$LIGHTTAG_REDIRECT_CHANGE_SET" \
  --region us-east-1 --profile 'local agent'
```

Use `make lighttag-redirect-deploy` only after DNS preflight, local checks, and
change-set review have passed. The deploy target executes the named change set;
it does not create one. Because CloudFormation does not expose a reliable
`ChangeSetType` field in the describe response, the target reads the
authoritative stack `StackStatus` immediately before execution: `REVIEW_IN_PROGRESS`
means `CREATE`, while approved stable complete/update-rollback states mean
`UPDATE`; transitional or failed states are rejected. A supplied type must
match that derivation. The target then waits for stack completion and
distribution deployment, enables termination protection, and reports stack
outputs. Record the stack ID, distribution ID/domain, certificate ARN, and
change-set ARN in the change ticket; do not put those environment-specific
values in this repository.

For a template rollback, first inspect stack events and then create a new change
set from the known-good revision. An executed change set is not reusable. Do not
delete the distribution, certificate, hosted zone, or DNS records as a rollback
shortcut. For a DNS rollback, follow the delegation procedure above and restore
the saved authoritative records.

Useful read-only and recovery commands are:

```sh
aws cloudformation describe-stack-events \
  --stack-name "$LIGHTTAG_REDIRECT_STACK" \
  --region us-east-1 --profile 'local agent'
aws cloudformation describe-stacks \
  --stack-name "$LIGHTTAG_REDIRECT_STACK" \
  --region us-east-1 --profile 'local agent'
# Only when the stack is UPDATE_ROLLBACK_FAILED and the skipped resources are
# understood; otherwise stop and obtain owner approval.
aws cloudformation continue-update-rollback \
  --stack-name "$LIGHTTAG_REDIRECT_STACK" \
  --region us-east-1 --profile 'local agent'
```

For a known-good template, create a new reviewed change set from that revision
and execute it with `make lighttag-redirect-deploy` using its explicit change
set name. CloudFormation's automatic rollback on a failed create/update must
finish before another change is attempted.

The typed live validator covers the legacy host set. Before the registrar cutover,
the connect-target form is required: it reaches the CloudFront distribution
while preserving each logical legacy hostname in `Host` and TLS SNI. Do not use
the default public-DNS form before cutover. After delegation, run the default
form from at least two independent resolvers:

```sh
# Before cutover, with distribution_domain discovered from the stack output.
make lighttag-redirect-live-test \
  LIGHTTAG_REDIRECT_LIVE_ARGS="--live --connect-host $distribution_domain"

# After registrar delegation and resolver convergence.
make lighttag-redirect-live-test
```

The typed live validator checks the apex, `www`, and guide hosts, root/guide
aliases, unknown paths, direct HTTP and HTTPS edge `301`/`410` behavior (no
HTTP-upgrade hop), `GET` and `HEAD`, slash/case variants, the historical typo
and its compatibility alias, DNS/TLS on IPv4 and IPv6, one-hop chains, and
destination canonicals. For every article row, it must assert one exact `301`,
an absolute `Location` on the fixed production host, the expected destination
path, and no query string in the `Location`. It must also assert that an
unknown path returns `410 Gone` and that no response falls back to an unrelated
article. The default public-DNS form must run only after delegation and from at
least two independent resolvers. Before cutover, use the connect-target form;
it preserves the logical hostname in both `Host` and TLS SNI:

```sh
uv run infra/lighttag-redirects/validate.py --live \
  --connect-host "$distribution_domain"
```

## Adding a future redirect

1. Add the article as a normal Hugo page bundle and include complete
   `[original_publication]` provenance: `site = "LightTag.io"` and the exact
   historical `path` (including case, spelling, and whether the slash was
   present).
2. Add exactly one source-to-destination row to the CloudFormation map and
   this table. Use the bundle's canonical `/en/posts/lighttag/<slug>/` path;
   never point back to LightTag and never silently correct the source key.
3. Run the local test, provenance validator, `cfn-lint`, and a rendered change
   set. Have the implementation owner and Sol reviewer approve the diff.
4. Deploy through a reviewed change set and run the live test for the new row.
   Keep the old row forever unless the owner documents a deliberate 410 change.

## Phase 2: search migration and monitoring

Phase 2's external search submissions are intentionally not part of `make
validate`, CI, or any deployment target. The offline IndexNow collector and
protocol tests are included in `make validate`; they do not contact IndexNow.
Only an owner-approved, explicitly confirmed submission may contact a search
engine.

### Google Search Console

- [ ] Verify production DNS, TLS, and the complete live redirect matrix first:
      every old article URL returns one `301`, every new canonical returns
      `200`, and `guide.lighttag.io` and unknown paths remain intentional
      `410 Gone` responses.
- [ ] In one Google account, verify `lighttag.io` (Domain property),
      `www.lighttag.io` (URL-prefix property), and `talperry.com` (Domain or
      URL-prefix property). Use the existing apex TXT token for LightTag and
      never overwrite the apex SPF, `Authenticate Domain`, or another owner's
      verification token. See [Google's ownership verification
      guide](https://support.google.com/webmasters/answer/9008080).
- [ ] Confirm the production XML sitemap, robots policy, canonical tags, and
      language alternates contain only the new site URLs. Submit
      `https://talperry.com/sitemap.xml` in Search Console.
- [ ] Use URL Inspection to inspect each old/new pair from the canonical map:
      inspect the old LightTag URL to confirm the `301` and then inspect its
      `https://talperry.com/en/posts/lighttag/<slug>/` destination. Record the
      inspection result and timestamp; request recrawl only for approved
      destination URLs. URL Inspection is documented in [Google's URL
      Inspection guide](https://support.google.com/webmasters/answer/9012289).
- [ ] After production is live and the redirect matrix is verified, use
      Search Console's Change of Address for the apex/www move to
      `talperry.com`; do not run a move for `guide.lighttag.io`, which is
      intentionally retired with `410 Gone`. This tool is for a completed move
      with redirects, as described in [Google's Change of Address
      guide](https://support.google.com/webmasters/answer/9370220).
- [ ] Do not send Google submissions through IndexNow. Use Search Console's
      sitemap and URL Inspection workflows; record account, timestamps, and
      any response or request IDs. Never submit from tests or CI.

### Bing Webmaster Tools and IndexNow

- [ ] Import the verified `lighttag.io`, `www.lighttag.io`, and `talperry.com`
      properties from the same Google account into Bing Webmaster Tools, then
      confirm the imported ownership and sitemap entries. Bing documents this
      workflow in [Add and verify a site](https://www2.bing.com/webmasters/help/add-and-verify-site-12184f8b).
- [ ] Submit `https://talperry.com/sitemap.xml` to the `talperry.com` Bing
      property and review the sitemap processing report. See [Bing's sitemap
      guidance](https://www.bing.com/webmasters/help/sitemaps-3b5cf6ed).
- [ ] After the P2.A IndexNow review and owner approval, recursively collect
      and submit **every canonical Tal Perry page in every language** from
      `https://talperry.com/sitemap.xml` and all of its sitemap-index children.
      This is the complete sitemap URL set, not only changed/new pages or the
      LightTag `/en/` pages. Deduplicate URLs and submit the resulting batches
      once to the single global IndexNow endpoint; do not post duplicate copies
      separately to each participating engine. The current production sitemap
      fits in one batch. Run the guarded command once and pipe both stdout and
      stderr through `tee` into a dated change-record log:

      ```sh
      set -o pipefail
      export INDEXNOW_LOG="/path/to/change-records/indexnow-$(date -u +%Y%m%dT%H%M%SZ).log"
      if ! make submit-indexnow INDEXNOW_CONFIRM='SUBMIT INDEXNOW' 2>&1 | tee "$INDEXNOW_LOG"; then
        echo "IndexNow submission failed; inspect $INDEXNOW_LOG" >&2
        exit 1
      fi
      ```

      Retain the script's evidence for every batch: submission timestamp,
      HTTP status (`200` or `202`), URL count, response-body SHA-256 and byte
      count, and any `Retry-After` value, plus the Bing IndexNow report. If a
      batch returns HTTP `429`, stop; honor its `Retry-After` value and never
      use an automatic retry. For the current one-batch production run, rerun
      the sole batch only after that wait and only when no success evidence was
      recorded for it. If a future multi-batch run partially fails, stop and
      add reviewed resume/batch-selection support before retrying; never
      blanket-rerun the full sitemap or repost a batch already recorded as
      successful. Do not use IndexNow for Google or for the retired guide URLs;
      it is a crawl signal, not an indexing guarantee. See the [IndexNow
      protocol documentation](https://www.indexnow.org/documentation).

### Other search engines

The global IndexNow endpoint distributes a valid submission to participating
engines discovered dynamically. Acceptance, processing, and indexing are not
guaranteed for any particular participant. Do not make duplicate per-engine
posts or claim global delivery/indexing from one successful submission.
There is no approved automation for DuckDuckGo, Yahoo, Brave, or Baidu in
this migration. Do not invent endpoints or submit credentials; let those
engines discover the canonical sitemap and redirects through normal crawling.

### Monitoring cadence

- [ ] At 24 hours, check Search Console and Bing for sitemap processing,
      redirect chains, soft 404s, crawl errors, canonical selection, and
      indexed legacy URLs; check CloudFront/distribution and certificate
      health.
- [ ] Recheck the same signals weekly for the first month, then monthly while
      the migration settles. Keep the redirect stack for at least one year and
      preferably indefinitely.
- [ ] Monitor aggregate CloudFront request volume, 4xx/5xx rates, Function
      errors and utilization, cache/error behavior, and distribution/certificate
      health. Intended `410 Gone` responses contribute to aggregate 4xx, so use
      the deliberate synthetic validator to distinguish expected traffic from
      failures. Alert on 5xx or function-error spikes, redirect loops,
      certificate/alias failures, or an aggregate 4xx change suggesting a
      missing historical row. Keep change-set, DNS, submission, and dashboard
      snapshots with the change record.
