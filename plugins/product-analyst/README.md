# Product Analyst

Product Analyst is a Claude Code plugin for bounded, evidence-backed product investigations. It combines a read-only PostgreSQL gateway with read-only PostHog and Amazon QuickSight research. It creates no dashboards, insights, cohorts, analyses, exports, or other persistent analytics artefacts.

Use `/product-analyst:investigate` for a metric question or a suspected product change. The skill reads the project's agreed metric definitions, resolves an analytical contract before it queries, records evidence for each source call, and has an independent verifier record a verdict for every claim before the findings are published. A second verifier then checks that the report's own wording says what those claims say before the report is written.

## Install and configure

Register this plugin from the repository marketplace, then add `.analyst/config.toml` and `.analyst/metrics.toml` to the analysed project from the files in `setup/`. Replace all example values. Optionally add `.analyst/context.toml`, the analysis context described in `skills/investigate/references/setup.md`. The plugin requires Claude Code 2.1.281 or later, Python 3.11 or later on `PATH` for hooks, and `uv` for its MCP server. Its MCP server uses `${CLAUDE_PROJECT_DIR}` to scope configuration and investigation records to the analysed project. QuickSight use needs the AWS CLI. Docker is optional and used only for the PostgreSQL integration test. The gateway adds its local `.analyst/investigations/` ignore rule when it starts an investigation.

The plugin's hooks act only in a project that has `.analyst/config.toml`. In any other project they give no opinion, so enabling the plugin does not change how PostHog or the AWS CLI behave there.

For PostHog, configure a connector named `posthog` in the analysed project's `.mcp.json`; `skills/investigate/references/posthog.md` shows a read-only entry for PostHog's hosted server. The plugin does not change connector settings. Names containing `posthog` may also be classified by the hook, but use the required name instead of relying on alias matching. The skill supports the documented CLI discovery and `call` wrapper forms. A connector configured with `mode=tools` and a server-side `tools=` allowlist may expose only the exact direct read-tool list in `skills/investigate/references/posthog.md`; discovery remains available through the CLI wrapper.

The PostgreSQL MCP server takes a libpq service name. Put connection details in `~/.pg_service.conf` and credentials in `~/.pgpass`, not in the project or plugin configuration. A service name is a standard libpq indirection; see the [PostgreSQL documentation](https://www.postgresql.org/docs/current/libpq-pgservice.html).

Attach a database role that can only select approved schemas, a PostHog key scoped to the necessary read APIs, and the supplied QuickSight read-only IAM policy. Those credentials enforce access. The plugin's guards reduce accidental misuse but are not the primary security boundary.

## Investigation records

An investigation writes local evidence under `.analyst/investigations/<id>/`:

- `contract.json`: resolved metric, population, time window, timezone, and comparison;
- `sources.json`: fingerprints of the configuration, metric catalogue and analysis context used by this investigation, including every file the context references;
- `context.json`: the analysis context as it was when the investigation started, or null;
- `evidence.jsonl`: evidence records from gateway and allowed source calls;
- `candidates/`: candidate findings stored by `prepare_findings`, named by their SHA-256;
- `verifications.jsonl`: verifier verdicts, each bound to one candidate, the contract and the source fingerprints;
- `findings.json`: the published claims with citations, verdicts, uncertainty, and stop reason;
- `reports/`: report versions stored by `prepare_report`, each with the author's narrative, the assembled text, its blocks and the hashes it is bound to;
- `report_verifications.jsonl`: report-verifier verdicts, each bound to one report version;
- `report_acceptances.jsonl`: the report versions `check_report` accepted;
- `report.md`: the reader-facing result, written only by `check_report`.

Keep these records local unless your team's evidence-retention policy says otherwise. Changes to `.analyst/config.toml`, `.analyst/metrics.toml`, `.analyst/context.toml` or a file the context references require a new investigation; the gateway rejects queries, verdicts, final claim checks and report checks when their recorded fingerprints drift. It does not read or fingerprint libpq service and password files.

`check_claims` publishes a prepared candidate only when, if it contains claims, its one verification covers every claim under the unchanged contract and sources. A verdict of `supported` on a data claim must cite evidence recorded after the first candidate was prepared that no claim cites, and `SUPPORTED` or `REFUTED` needs a supported data claim and no refuted claim. The gateway checks that the verification is current and complete; it does not check who wrote it, and it cannot tell whether a number is right; numerical correctness rests on the verifier. A context claim's text must be the fixed text of the analysis-context statements it cites.

The investigator writes only the report's title, answer and explanation. `prepare_report` refuses any number in them that the published findings and contract do not contain, then assembles the report: that narrative, followed by the contract, every claim with its verdict and limitations, the uncertainty and the stop reason, copied from the published findings. It keeps the narrative byte for byte, so a line break made with two trailing spaces survives, and refuses carriage returns. It stores the result as a version bound to the exact report bytes, the published findings, contract, sources, renderer version, the report verifier's instructions and the rule of the recorded stop reason, so changed instructions or a changed rule void earlier verdicts. The report verifier reads a version through `get_report_verification_input`: the version's hashes, the narrative and its blocks, and the full contract, every published claim, the uncertainty, the stop reason and the rule of that reason, without the evidence, sources or other versions. Claude Code saves a tool result over 50,000 characters, counted in UTF-16 code units, to a file, which the verifier has no tool to read. So an input over 40,000 units is never cut: `prepare_report` refuses a narrative whose input would be that long, and the tool returns only an error for it. The tool also returns only errors for a version that is no longer intact or current, is already verified, or belongs to an investigation that has used its two verifications. The report verifier records a verdict for every block of the narrative, and on whether the title and answer keep the limits of their claims, once per version; an investigation allows two such verifications. A statement of the stop reason, and of why the investigation stopped, is checked against the stop reason, its rule and the claims. A block that says nothing about the data, such as a table header, a labelled example query or a note on how the report was written, is recorded as non-analytical and supported; anything a block says about the data, a metric, a source or how a value was obtained is checked against the basis. `check_report` writes `report.md` only for a version that is unchanged, still current and supported in every block, and it creates `report.md` in one step and only where no file exists. It never overwrites one: an existing `report.md`, even an empty one or an earlier accepted version, is kept and reported as a conflict to resolve by moving it aside. After a report is accepted, `check_claims` refuses to publish other findings in that investigation. The narrative is held to a strict Markdown subset, with no headings, HTML, images, footnotes or unclosed code blocks, so it cannot reach into the copied sections. These checks establish that the verdicts cover the exact text a reader gets. As with claim verdicts, the gateway does not check who records the report verdicts, and whether the verifier judged the meaning correctly has not been measured, so a person still reads the report.

Keep the PostgreSQL service target and PostHog project connection stable during an investigation. Start a new investigation if either source connection changes because those external identities are outside the local source fingerprints.

## Limits

The gateway restricts database SQL to a narrow read-query subset and runs it as a single prepared statement in a read-only transaction, so PostgreSQL itself refuses a second statement. A refused query returns the reason to the caller; connection failures stay generic because their messages can name hosts and users. It does not make aggregate data non-sensitive. Database grants must enforce approved schemas, row-level security, and any small-cell or privacy policy.

The PostHog hook applies its read allowlist to recognised PostHog connector calls. The QuickSight hook permits literal, direct AWS CLI read commands only, and denies any other command that names both `aws` and `quicksight`. Permitted calls get no opinion from the hooks, so your own permission rules still decide whether they run. Shell aliases, constructed commands, encoded commands, unrelated connector aliases, disabled hooks, and outer hook launch failures or timeouts can bypass those classifiers. The pre-tool supervisor converts malformed input and child guard errors into a denial before its own deadline. Use least-privilege database grants, PostHog key scopes, and a QuickSight IAM principal restricted to the supplied read-only policy as the security boundary; hooks are a second layer.

## Verify the plugin

Run these commands from the repository root:

```sh
python3 -m unittest discover -s plugins/product-analyst/tests -p 'test_*.py'
python3 plugins/product-analyst/scripts/check_posthog_tools.py
ANALYST_TEST_MCP=1 python3 -m unittest discover -s plugins/product-analyst/tests -p 'test_mcp_runtime.py'
bash plugins/product-analyst/tests/run_postgres_integration.sh
```

The runtime smoke test uses the locked `uv` MCP environment without a database. The integration script starts a temporary PostgreSQL 16 Docker container and removes it when the script exits.

## References

- [Claude Code MCP configuration](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [PostgreSQL read-only transactions](https://www.postgresql.org/docs/current/sql-set-transaction.html)
- [Amazon QuickSight API operations](https://docs.aws.amazon.com/quicksight/latest/developerguide/analysis-operations.html)
