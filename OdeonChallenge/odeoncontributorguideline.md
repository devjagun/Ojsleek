Contributor Guide
How to create evaluation datapoints for this pipeline. Read end-to-end before building anything.

Section 1
What You're Building
Each datapoint is a self-contained investigation problem. You provide live infrastructure (databases, APIs, services) with a realistic data environment and a deliberately planted problem. An AI agent receives a short, underspecified prompt and must figure out what's going on by querying the live services, analyzing data, reading code, and synthesizing findings — and then take action to fix it.

The agent has full shell access inside a sandboxed environment. It can run SQL queries, call APIs with curl, write and execute Python scripts, read source code, modify configuration, and explore freely. Your job is to build an environment that rewards thorough, multi-step investigation and penalizes shallow analysis.

The agent must both diagnose and fix. The expected outcome is not just a writeup — the agent should investigate the problem, explain what it found, and then take concrete action to resolve it. This could mean rolling back a deployment flag, correcting a misconfigured parameter, patching a buggy function, or fixing a data pipeline. The verifier checks that the fix was actually applied and working.

Every problem must require data science and analytical skills to solve. The problem can lean towards software engineering in its nature — debugging a production incident, tracing a deployment regression, investigating a performance degradation — but the path to the answer must go through data. The agent should need to query databases, analyze logs quantitatively, join data across sources, form and test hypotheses, compute metrics, and distinguish real causes from noise. A problem that can be solved by reading code alone, without touching the data, is not a valid datapoint.

Good — requires DS/analytics	Bad — pure SWE
"Costs jumped 18%" — agent must query billing data, join with hedging positions, compute coverage ratios, and quantify the gap	"The login page is broken" — agent reads an error traceback and fixes a typo
"Jobs are failing" — agent must analyze completion rates by hardware type, correlate with topology specs, and identify the statistical pattern	"Add a caching layer to the API" — agent writes code, no data analysis needed
"Deployment caused a regression" — agent must pull metrics before/after, segment by user cohort, and isolate which change drove the regression	"Update the config to use the new DB host" — agent edits a config file
Section 2
Core Principles
Three non-negotiable requirements for every datapoint.

1 Production realism
Your environment must feel like a real production system, not a toy demo. This means depth over quantity — a few well-built services with realistic internals beat a dozen shallow ones.

Mix your tech stack. Real companies don't build everything in one language. Your application services (the company's own code) should use a heterogeneous stack — a Go API gateway, a Python ML serving layer, a Rust data pipeline — each with their own idioms, error handling patterns, and logging formats. Don't write every backend in Flask/FastAPI. Your data services (mocked external platforms like _stripe, _posthog) can be simpler since the agent won't see their code — focus on faithfully mocking the real platform's API. See Section 5.1 for the full distinction.

Good	Bad
Order service in Go, analytics pipeline in Python, search indexer in Rust	Five Python Flask apps with identical structure
PostgreSQL for transactional data, Redis for caching/sessions, S3-like blob store for exports	Everything in one Postgres database
REST API for the main product, gRPC between internal services, GraphQL for the dashboard	Every service exposes identical REST endpoints
Mix your API formats and conventions. Different services in a real company have different API styles, authentication methods, error formats, and documentation quality. One service might return well-structured JSON with pagination; another might return XML or CSV dumps; a third might have inconsistent error codes. This is realistic and tests whether the agent can navigate heterogeneous systems.

Use git history, not changelogs. Real engineers discover what changed by reading git logs and diffs, not by consulting a tidy changelog.md. Your environment/ directory should be a monorepo — a single git repository containing all application services (not _-prefixed data services), just like a real company codebase. The agent should be able to git log, git diff, and git blame to trace when a bug was introduced or a config was changed.

For example, instead of:

environment/pricing_service/changelog.md
  - 2025-01-15: Updated spread calculation formula
The agent should see:

$ git log --oneline
a3f1c2d fix(pricing): handle null spreads in edge case
9e8b7a6 feat(analytics): add weekly aggregation pipeline
4d5e6f7 refactor(pricing): extract calculator into module
b2c3d4e fix(gateway): correct timezone handling in settlement window
7f8a9b0 feat(pricing): add basis-point spread override
e1d2c3b chore: update Go dependencies across services
Commits should span services naturally. Real monorepos have commits that touch multiple services — dependency updates, cross-cutting refactors, coordinated feature work. Don't make every commit single-service; mix in commits that touch shared config, update multiple services at once, or change infrastructure-level concerns.

Bug-introducing commits must blend in. The commit that introduces the bug or misconfiguration cannot be the only commit touching that service or file. It must be surrounded by other legitimate changes to the same area. A single suspicious commit that stands out from everything else is too easy for the agent to spot. The problematic change should be buried in a commit that also does something reasonable — a refactor that subtly breaks a formula, a dependency update that changes default behavior, a config change that adjusts multiple values where one is wrong.

How to ship git history using patches: Datapoints are submitted via PR to a git repo. Since git ignores nested .git directories, you can't just check in a .git folder — it will be lost. Instead, export your monorepo's history as git format-patch files (plain text, fully reviewable in PR diffs). The pipeline reconstructs the repo automatically before running setup.sh.

Step 1 — Build the monorepo locally inside a temporary directory:

mkdir /tmp/my_monorepo && cd /tmp/my_monorepo
git init
# Copy in your application service dirs and make commits
cp -r /path/to/pricing_service . && git add pricing_service/ && git commit -m "feat(pricing): initial pricing engine"
cp -r /path/to/gateway . && git add gateway/ && git commit -m "feat(gateway): add API gateway with routing"
# ... build up history with commits spanning multiple services
Use meaningful messages, realistic author names, and dates that tell a story. Interleave work across services — don't commit all of service A, then all of service B.

Only include application service code in the git history. Do not commit any of the following to your monorepo (and therefore do not include them in patches):

•
_-prefixed data service directories (_stripe/, _posthog/, etc.)
•
Infrastructure files (docker-compose.yml, setup.sh, healthcheck.sh, generate_data.py)
•
Top-level .md files (prompt.md, endpoints.md)
•
Seed data directories (_seed_data/)
These files belong in environment/ only. If they appear in patches, they get committed to git history and then deleted during workspace cleanup — polluting the judge's git diff HEAD with deletions unrelated to the agent's work.

Step 2 — Export patches:

cd /tmp/my_monorepo
git format-patch --root -o /path/to/datapoints_loading/<name>/environment.patches/
This creates one numbered .patch file per commit in environment.patches/ at the datapoint root. These are plain text files that will be reviewed in your PR.

Step 3 — Check in the patches directory alongside environment/:

datapoints_loading/<name>/
├── environment/              # All services + infra files (no .git/)
│   ├── pricing_service/
│   ├── gateway/
│   ├── _posthog/
│   ├── docker-compose.yml
│   ├── setup.sh
│   ├── prompt.md
│   └── ...
├── environment.patches/      # Exported git history (app services only)
│   ├── 0001-feat-pricing-initial-engine.patch
│   ├── 0002-feat-gateway-add-routing.patch
│   ├── 0003-feat-analytics-add-pipeline.patch
│   ├── 0004-chore-update-dependencies.patch
│   ├── 0005-fix-pricing-handle-null-spreads.patch
│   └── ...
└── ground_truth/
Check in both environment/ and environment.patches/. The codebase files are needed for Docker builds; the patches give the agent git history to investigate.

The pipeline validates and reconstructs automatically. During Stage 1 (before upload), validate_patches() runs three local checks on every datapoint with patches:

•
Forbidden files (hard error) — patches must not contain _-prefixed dirs, infra files, top-level .md files, or _seed_data/. These are removed during workspace cleanup and would pollute the judge's git diff HEAD.
•
Consistency (hard error) — the final state after applying all patches must match the corresponding files in environment/. A mismatch means the agent sees different code than what git history shows.
•
Coverage (warning) — app-service files in environment/ that have no patch history are flagged. This may be intentional (e.g. auto-generated files) but is worth reviewing.
Datapoints that fail checks 1 or 2 are removed from the run. At runtime, the pipeline copies environment/ contents into /workspace/, stashes .md files, runs git init, removes any files that the patches will create (to avoid conflicts since environment/ contains the final state), then runs git am to apply the patches and reconstruct git history. .md files are restored as untracked. If no patches exist, everything is committed as an initial commit (excluding .md files). The agent sees a normal git monorepo with full history. Your setup.sh does not need any patch-related logic.

Patches are optional. Not every datapoint needs git history. If your investigation doesn't require git log / git blame, skip patches entirely — the datapoint will work fine without them.

Give application services realistic internals. Each application service should have real configuration files, logging output, and the kind of incidental complexity you find in production. A Go service should have a go.mod, structured logging with slog, and realistic error wrapping. A Python service should have a requirements.txt with pinned versions and standard project layout. Data services (_-prefixed) don't need this depth since the agent can't see their code — focus on faithfully mocking the external platform's API instead.

Every application service should have a README. Real codebases have READMEs — the agent should too. Each application service directory under environment/ should include a README.md that covers what the service does, how it fits into the overall system, its key configuration, and how to run it locally. Quality will naturally vary — some READMEs will be thorough, others sparse or slightly outdated, just like in a real production system. That's fine. The README is how the agent orients itself when exploring an unfamiliar codebase — without one, the environment feels artificial. Never hint at the planted problem. Data services don't need READMEs — document their APIs in endpoints.md instead.

2 Fairness
A competent human must be able to solve the problem. This is a hard requirement. If a skilled engineer or data scientist with relevant domain knowledge couldn't reasonably arrive at the correct answer given the available information, the datapoint is broken — no matter how clever the design.

Fairness means:

All necessary information is accessible. Every piece of evidence the agent needs to reach the correct conclusion must exist somewhere in the environment — in the data, the APIs, the code, or the configuration. If the root cause requires knowledge that isn't present in the sandbox, the problem is unfair.

The investigation path is discoverable. There must be a logical chain of reasoning from what the agent can observe to the root cause. Each step should follow naturally from the previous one. If finding the answer requires a lucky guess or an unintuitive leap with no supporting evidence, redesign the problem.

Clues are not hidden behind unreasonable barriers. The agent should need analytical skill to find the answer, not esoteric tool knowledge. Don't require obscure CLI flags, undocumented API parameters, or decoding binary formats that a competent person wouldn't know how to handle. The difficulty should come from the analytical reasoning, not from access mechanics.

The rubric does not punish reasonable alternative approaches. If a skilled analyst could legitimately reach the correct conclusion through a different investigation path than the one in your ideal walkthrough, they should still score well. Avoid criteria that require a specific sequence of steps when the conclusion is what matters.

Red herrings are distinguishable from the real cause. It must be possible — with sufficient analysis — to rule out every red herring using information available in the environment. If a red herring is indistinguishable from the real root cause given the available data, the problem is unfair.

The human test
Before submitting, walk through the problem yourself as if you were seeing it for the first time:

•
Read only the prompt and endpoints.md (if provided)
•
Explore the environment using only what's in /workspace/
•
Follow the evidence chain to the root cause
•
Verify that every rubric criterion is achievable with the information available
•
Check that every red herring can be ruled out with available data
If you get stuck at any point and need to reference your own ground_truth/ files to figure out what to do next, the problem needs work.

3 Difficulty calibration
Target: the best available agent should score below 30% on a well-designed problem. The problem must be hard — but hard because of analytical depth, not because of unfairness.

This means:

•
Multiple hypotheses need to be formed and tested before the root cause emerges
•
Data sources require several joins and reconciliations to reveal the signal
•
At least one red herring must be pursued and ruled out with evidence
•
The fix requires understanding the root cause deeply enough to know what to change
•
The agent must write and execute scripts, not just read files
Hard for the right reasons, not the wrong ones. Difficulty should come from the depth of the analytical reasoning, the number of data sources that must be cross-referenced, and the subtlety of the root cause — not from missing information, ambiguous prompts, or requiring domain-specific esoteric knowledge.

Hard for the right reasons	Hard for the wrong reasons
Root cause requires correlating 4 data sources across 3 services	Root cause requires knowing an obscure Postgres GUC parameter by heart
Signal is statistically subtle — appears only when you segment by the right dimension	Signal is hidden behind an undocumented API endpoint
Red herring has strong surface-level evidence that takes real work to disprove	Problem has two equally valid root causes and the rubric only accepts one
Fix requires understanding a complex code path to know what to change	Fix requires writing code in an uncommon language/framework with no docs available
Proxy for difficulty: Before submitting, enumerate the distinct investigation steps a skilled analyst would take. If you can list fewer than 10 non-trivial steps, the problem is probably too easy. If a skilled analyst couldn't complete it in under 2 hours, it might be too hard or unfair.

Section 3
Datapoint Structure
Every datapoint lives in datapoints_loading/<name>/ and must contain these files:

datapoints_loading/<name>/
├── environment/                # REQUIRED — everything the sandbox needs
│   ├── docker-compose.yml      # REQUIRED — defines services (DBs, APIs, apps)
│   ├── setup.sh                # REQUIRED — builds and starts all infrastructure
│   ├── healthcheck.sh          # REQUIRED — verifies all services are ready
│   ├── generate_data.py        # REQUIRED if data is synthetic — deterministic seed data
│   ├── _seed_data/              # Generated data mounted by Docker services
│   ├── pricing_service/        # Application service (code visible to agent)
│   ├── gateway/                # Application service (code visible to agent)
│   ├── _posthog/               # Data service (deleted before agent runs)
│   ├── _stripe/                # Data service (deleted before agent runs)
│   ├── prompt.md               # REQUIRED — what the agent sees (untracked in git)
│   ├── endpoints.md            # Optional — API reference for the agent (untracked in git)
│   └── ...
├── environment.patches/        # Optional — git history for application services only
└── ground_truth/               # REQUIRED — hidden from agent, used by judge
    ├── rubric.json             # Scoring criteria, penalties, programmatic checks
    ├── facts.md                # Ground truth: root cause, red herrings, key metrics
    ├── verifier.py             # Programmatic checks against live services
    ├── golden_response.md      # Expert-written ideal response
    ├── golden_solution.py      # Reference solution (run by pipeline pre-check)
    └── solution.md             # Human-readable solution walkthrough (not read by judge)
The environment/ directory is the complete sandbox contents. At runtime, the pipeline copies its contents into /workspace/, git-initializes it (applying patches if present or committing everything), brings up infrastructure, and then cleans the workspace for the agent — keeping only non-_-prefixed directories and top-level .md files. The agent sees a realistic git-tracked codebase with application services, prompt.md, and endpoints.md.

ground_truth/ is uploaded separately and is only visible to the judge.

Agent report location: The agent writes its response/report to response.md in /workspace/. Your prompt should instruct the agent to write its findings there. Do not expect the report to appear anywhere else, and do not have verifier.py read the report (see Section 8.3).

Section 4
Writing the Prompt
The prompt goes in environment/prompt.md. It should read like something a real person would say to a data scientist — short, situational, and underspecified.

Underspecified means the agent must figure out what to investigate. The prompt gives a situation and a vague goal, not a step-by-step plan. Real stakeholders don't write structured briefs.

Good prompt
I'm an analyst at BrightGrid Energy. Operations flagged that power procurement costs jumped 18% last month despite stable demand. Finance says our hedging contracts should have covered this. The trading desk blames "market volatility" but wholesale prices only moved 3%. Something doesn't add up. Can you dig into our systems and figure out what's actually driving the cost increase?

This names a problem, includes a plausible-but-possibly-wrong explanation (market volatility), and doesn't tell the agent where to look.

Bad prompt
Query the postgres database for the pricing_forecasts table. Join it with the hedging_positions table on contract_id. Calculate the delta between forecasted and actual procurement cost per MWh. Plot the results by week. Check if the ARIMA model coefficients drifted.

That's a numbered to-do list, not an investigation. A prompt like this defeats the purpose of the eval.

Prompt rules
•
Keep it short. 2-4 sentences is ideal. The prompt is a Slack message or a brief email, not a requirements doc. All the context the agent needs to investigate should come from exploring the environment, not from reading a long prompt.
•
Include one plausible misdirection. A hypothesis from someone in the company that sounds reasonable but isn't the real cause.
•
Don't name specific files, tables, or endpoints. The agent should discover these on its own.
•
Don't hint at the answer. No column names like root_cause_flag or files named the_real_problem.csv.
Service documentation (important)
Real production environments have documentation. Your environment should too. The prompt stays short because the agent discovers context from docs that exist in the workspace — just like a real engineer joining an investigation.

Include realistic documentation alongside your services:

•
README.md in each application service directory — architecture overview, how to run locally, key design decisions. Quality can vary (some thorough, others sparse or outdated — just like real production systems). Data services (_-prefixed) don't need READMEs since the agent can't see their source dirs.
•
endpoints.md — API reference for all services the agent can query, including data services. For data services, this is the primary documentation the agent has. Match the real platform's API docs style where possible.
•
Runbooks or playbooks — operational docs for common issues (the current issue shouldn't be in the runbook, but related procedures should exist)
•
Architecture diagrams or descriptions — how services connect, data flow between systems
•
Inline code comments — realistic comments in the codebase, not breadcrumbs to the answer
This documentation serves two purposes: it makes the environment feel real, and it gives the agent legitimate context to work with so the prompt can stay concise. The agent should be able to orient itself by reading docs in the workspace, not by being told everything upfront.

Section 5
Designing the Data Environment
The data environment is where the complexity lives. You're building a miniature production system that contains a real, discoverable problem buried across multiple data sources.

1 Infrastructure components
Your docker-compose.yml defines the live services. There are two types of services, and the distinction matters for how you build them and how the agent interacts with them.

Data services (prefixed with _)
Data services are mocked external platforms — things like Stripe, PostHog, Datadog, Snowflake, or any third-party API your scenario's company would use but not own. They exist to provide realistic data sources for the agent to query, not to contain bugs.

Name these with a leading underscore: _posthog, _stripe, _datadog. Place their source code under environment/_posthog/, environment/_stripe/, etc. The _ prefix tells the pipeline to delete these directories (along with other non-agent files) before the agent runs — the agent can call their APIs but cannot read their code.

Data service APIs should faithfully mock the real-world counterpart. If you're mocking PostHog, your endpoints should match PostHog's actual API structure — the same URL patterns, query parameters, response shapes, pagination, and error formats. The agent may already know how to use these APIs from training; a faithful mock lets it apply that knowledge naturally. Don't invent custom API shapes when a well-known platform's API would be more realistic.

Data services:

•
Are bug-free — they serve data, not problems
•
Are not included in the git monorepo — no patches, no git history
•
Have their source code deleted before the agent runs (the pipeline cleans the workspace)
•
Are documented in endpoints.md, not per-service READMEs (since the agent can't see their source dirs)
Application services (no prefix)
Application services are the company's own codebase — the services built in-house where bugs, misconfigurations, and defects can live. These are what the agent investigates: reading source code, tracing git history, correlating code behavior with data.

Name these normally: pricing_service, gateway, analytics_pipeline. Their source code lives under environment/ and is fully visible to the agent.

Application services:

•
May contain the bug the agent needs to find and fix
•
Are included in the git monorepo with realistic commit history (see Section 2.1)
•
Have their source code visible to the agent
•
Should have a README.md — what the service does, how it fits into the system, key config, how to run it locally. Quality naturally varies — some will be thorough, others sparse or slightly outdated, just like in a real production system.
Putting it together
Type	Naming	Examples	Contains bugs?	Code visible?	Git history?	Docs
Data service	_-prefixed	_posthog, _stripe, _snowflake	No	No	No	endpoints.md
Application service	No prefix	pricing_service, gateway	Yes	Yes	Yes	Per-service README.md
Every service should be accessible from within the sandbox. Use Docker networking so the agent can reach services by hostname.

Application services should have realistic depth: proper project structure for its language, real configuration files, and logging. At runtime, the pipeline reconstructs /workspace/ as a git monorepo from patches (see Section 2.1).

2 Data realism
Data should look like it came from a real system, not a textbook exercise.

Match formats to their real-world source. A Stripe subscription object has nested cancellation_details with feedback and reason, not five flat columns. A Postgres analytics table has nullable fields, mixed timestamp formats, and orphaned foreign keys. A product changelog is a markdown file, not a database table.

Realistic volume. Hundreds to thousands of records minimum. Enough that the agent can't eyeball the answer — it must write queries and scripts.

Realistic messiness. Null values in fields that are sometimes unpopulated. Timestamps in different formats across sources. Duplicate records. Columns that look useful but aren't. Columns with unintuitive names that matter.

3 Data entanglement
This is the most important design principle. The root cause should only be discoverable by joining or cross-referencing multiple data sources. No single table or API endpoint should reveal the answer.

Strong entanglement patterns:

•
Two sources track the same metric but disagree — the agent must figure out which is correct and why
•
The key signal requires a 3-way join that isn't obvious from table/endpoint names
•
A field in one source contradicts what another implies — the agent must surface and resolve the conflict
•
A useful dimension is buried in one source and must be joined to unlock signal elsewhere
Good	Bad
Completion rates differ between the scheduler logs and the billing system — investigating why reveals the bug	All data is pre-merged into a single denormalized view
The topology constraint that causes failures lives in hardware specs and must be joined to job requirements	The root cause is visible in a single table with a column named failure_reason
Cost discrepancies only appear when you cross-reference three systems: forecasting, hedging, and settlements	Every data source is clean, consistent, and immediately usable
4 Red herrings
Every datapoint should include at least one red herring — a plausible-looking signal that doesn't hold up under deeper analysis. The agent should find it, investigate it, and conclude it's not the root cause.

Good red herrings:

•
Are real patterns in the data (not fabricated noise)
•
Look compelling at first glance (surface-level correlation)
•
Fall apart when you control for a confound or check a second source
•
Align with the misdirection in the prompt
5 Codebase as a data source
Don't limit your environment to databases and APIs. Real investigations often require reading application code. The agent can browse the source code of application services (non-_-prefixed) — a scheduler algorithm with a subtle bug, a pricing engine with an incorrect formula, a configuration file with a wrong value. Data services (_-prefixed) are opaque to the agent — it can only query their APIs.

The agent should be able to correlate what the application code does with what the data shows.

Section 6
Writing setup.sh
setup.sh is the entry point for bringing up your infrastructure. The pipeline runs bash /workspace/setup.sh after copying files into the sandbox. Docker is already running when your script executes.

Requirements
•
Must exit 0 on success, non-zero on failure
•
Must be idempotent (safe to run twice)
•
Should use set -euo pipefail at the top
•
Must use SCRIPT_DIR for paths (the script runs from /workspace/)
What it should do
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# 1. Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }

# 2. Generate seed data (if using generate_data.py)
if [ ! -f "$SCRIPT_DIR/_seed_data/some_file.csv" ]; then
    cd "$SCRIPT_DIR"
    python3 generate_data.py
fi

# 3. Build Docker images
docker compose -f "$COMPOSE_FILE" build --quiet

# 4. Start containers
docker compose -f "$COMPOSE_FILE" up -d

# 5. Wait for services to become ready
#    (poll database readiness, HTTP endpoints, etc.)

# 6. Verify key endpoints are responding
#    (curl health endpoints, check row counts, etc.)
Important notes
•
Do not use -p <project> with docker compose. Let it default to the directory name so the pipeline can auto-discover the compose network.
•
Do not exit until every service is ready to receive requests. This is critical. The pipeline runs setup.sh and then immediately runs healthcheck.sh. If setup.sh exits before all services are fully initialized (not just started, but accepting connections and returning valid responses), the healthcheck will fail and the eval will not run. Poll each service explicitly — databases accepting queries, HTTP endpoints returning 200s, message queues ready to consume. docker compose up -d returning is not sufficient; containers starting is not the same as services being ready.
•
Use docker compose -f "$COMPOSE_FILE" consistently. The compose file path must be explicit since the working directory may vary.
•
Keep python dependencies minimal. generate_data.py runs on the sandbox host, which has Python 3 but limited packages. Stick to the standard library plus csv, json, random, datetime. If you need more, install them in setup.sh.
Section 7
Writing the Healthcheck
Create healthcheck.sh inside environment/. This script runs inside a temporary Alpine container on the Docker compose network, after setup.sh completes and after DNS is configured. It serves as a final verification that all services are functional.

#!/bin/sh
# healthcheck.sh

# Install curl (runs in Alpine container)
apk add --no-cache curl > /dev/null 2>&1

# Check each service by its Docker hostname
curl -sf http://api-server:8000/health > /dev/null || { echo "FAIL: api-server"; exit 1; }
curl -sf http://nginx:80/health > /dev/null || { echo "FAIL: nginx"; exit 1; }

echo "All services healthy"
exit 0
The healthcheck runs with retries (up to 10 attempts, 5 seconds apart), so transient startup delays are tolerated.

Section 8
Ground Truth Files
All files in ground_truth/ are hidden from the agent and used only by the judge.

Prefer deterministic verification over LLM scoring
This is a key design principle. If something can be verified programmatically, it must be a programmatic check — not an LLM criterion.

Deterministic checks are more reliable, reproducible, and cheaper than LLM-based scoring. The LLM judge is powerful but non-deterministic; use it only for things that genuinely require judgment (quality of reasoning, completeness of explanation, nuance of recommendations).

Verifiable deterministically (use programmatic_checks)	Requires judgment (use criteria)
Agent rolled back a deployment flag	Quality of the agent's root cause explanation
A config parameter was changed to the correct value	Whether the agent's reasoning was sound
The correct SQL query was executed against the database	Completeness of the investigation narrative
An API endpoint now returns the expected response	Whether recommendations are specific and actionable
A specific file was modified or created	How well the agent distinguished root cause from red herrings
Service health improved after the agent's changes	Depth of quantitative analysis
Design your problems to maximize programmatic checkability. If the task involves fixing a misconfigured flag, rolling back a bad deployment, correcting a database record, or patching a config file — all of these outcomes can and should be verified by verifier.py querying the live services. Reserve LLM criteria for the analytical quality of the agent's writeup.

1 rubric.json
Defines the scoring structure. Three sections: criteria (LLM-scored), penalties (LLM-scored, negative), and programmatic checks (verifier-scored). Allocate as many points as possible to programmatic checks.

{
  "task_id": "energy_cost_investigation",
  "max_score": 100,
  "criteria": [
    {
      "id": "root_cause_explanation",
      "points": 15,
      "description": "Agent explains that the forecasting model uses stale basis-point spreads from Q2, causing systematic underhedging. Full credit requires naming the mechanism and showing how the stale config diverged from market conditions."
    },
    {
      "id": "red_herring_rejection",
      "points": 10,
      "description": "Agent investigates the 'market volatility' hypothesis from the trading desk and correctly concludes wholesale price movement (3%) cannot explain an 18% cost increase. Must show the math."
    }
  ],
  "penalties": [
    {
      "id": "blames_market_volatility",
      "points": -15,
      "description": "Apply if agent concludes market volatility is the primary cause without investigating the hedging model."
    },
    {
      "id": "vague_recommendations",
      "points": -5,
      "description": "Apply if recommendations are generic ('improve monitoring') without specific, actionable steps tied to findings."
    }
  ],
  "programmatic_checks": [
    {
      "id": "config_fixed",
      "points": 25,
      "description": "Agent updated bp_spread_override in config/settings.yaml to use live market rates (value between 300-320bp, not the stale 145bp)."
    },
    {
      "id": "service_restarted",
      "points": 15,
      "description": "Hedging service was restarted after config change and is running with the new config."
    },
    {
      "id": "hedging_coverage_improved",
      "points": 20,
      "description": "After the fix, the hedging coverage ratio returned by the API is above 90% (was 62% before)."
    },
    {
      "id": "queried_pricing_data",
      "points": 10,
      "description": "Agent queried the pricing database and retrieved forecast vs. actual spreads."
    },
    {
      "id": "quantified_impact",
      "points": 5,
      "description": "Agent's response.md contains a cost impact estimate within 20% of $2.14M."
    }
  ]
}
Note that 75 of the 100 points come from programmatic checks. The LLM criteria (25 points) cover only the things that require judgment: quality of the root cause explanation and red herring rejection. The fix itself — updating the config, verifying the outcome — is all verified deterministically.

Design principles
•
Put the majority of points in programmatic checks. The fix and its observable effects should carry the most weight. LLM criteria should cover the analytical reasoning that can't be checked programmatically.
•
Criteria descriptions must be specific. "Identifies the root cause" is too vague. Name the exact finding, the evidence required, and what partial credit looks like.
•
Penalties should target common wrong conclusions. If the prompt includes a misdirection ("the trading desk blames market volatility"), add a penalty for accepting it uncritically.
•
Programmatic checks verify observable outcomes. Did the agent fix the config? Is the service running correctly now? Did the metrics improve? These are checked by verifier.py against live services.
•
max_score must equal the sum of all criteria points + programmatic check points. Penalties are not counted in max_score (they subtract from earned points).
2 facts.md
The ground truth document the judge reads. Must have these sections:

Root Cause
Concise statement of the actual problem. Be specific — name the exact mechanism, the specific parameter, the precise data relationship.

Red Herrings
List each red herring, explain why it looks plausible on the surface, and explain why it falls apart under scrutiny. Include the specific data the agent would see that makes it look real.

Ideal Investigation Path
Ordered list of steps a skilled analyst would take. This helps the judge assess whether the agent's approach was methodical.

Key Metrics
Tables of concrete numbers the judge uses to verify the agent's calculations. The judge will compare the agent's reported numbers against these.

## Key Metrics

|
 Metric 
|
 Value 
|
 Source 
|
|
--------
|
-------
|
--------
|
|
 Excess procurement cost (Q3) 
|
 $2.14M 
|
 settlements table - hedging_positions join 
|
|
 Wholesale price change (Q3) 
|
 +3.1% 
|
 market_data API 
|
|
 Hedging coverage ratio (actual) 
|
 62% 
|
 hedging_positions table 
|
|
 Hedging coverage ratio (expected) 
|
 95% 
|
 hedging model config 
|
|
 bp_spread_override value 
|
 145bp 
|
 /etc/hedging/config.yaml 
|
|
 Current market spread 
|
 312bp 
|
 market_data API 
|
3 verifier.py
Runs programmatic checks against the live infrastructure. It makes API calls and database queries to verify specific things the agent should have found or done.

Required interface
import json
import sys
import os

def load_rubric():
    """Load rubric.json from the same directory as this script."""
    rubric_path = os.path.join(os.path.dirname(__file__), "rubric.json")
    with open(rubric_path) as f:
        return json.load(f)

def run_programmatic_checks() -> list[dict]:
    """Run checks against live services.

    Returns list of:
    {
        "id": "check_id",           # Must match rubric.json programmatic_checks.id
        "passed": True/False,
        "points_achieved": 10,      # 0 or points_total
        "points_total": 10,         # From rubric.json
        "detail": "Description of what was found"
    }
    """
    rubric = load_rubric()
    checks_def = {c["id"]: c["points"] for c in rubric["programmatic_checks"]}
    results = []

    # Example: check if the agent modified a config file
    config_modified = check_config_was_fixed()
    results.append({
        "id": "identified_config_param",
        "passed": config_modified,
        "points_achieved": checks_def["identified_config_param"] if config_modified else 0,
        "points_total": checks_def["identified_config_param"],
        "detail": "Config bp_spread_override was updated" if config_modified else "Config unchanged"
    })

    return results

if __name__ == "__main__":
    results = run_programmatic_checks()
    output_path = sys.argv[1] if len(sys.argv) > 1 else "verifier_output.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    # Exit non-zero if any check failed
    if not all(r["passed"] for r in results):
        sys.exit(1)
Host resolution pattern
Your verifier runs inside the sandbox where Docker service names may or may not resolve directly. Use this pattern to handle both cases:

import socket

def get_host(service_name, port):
    """Try DNS resolution first; fall back to localhost with Host header."""
    try:
        socket.getaddrinfo(service_name, port)
        return service_name, {}
    except socket.gaierror:
        return "localhost", {"Host": service_name}
What to check
•
API responses: Query endpoints and verify expected data is present
•
Database state: Connect and run queries to check if the agent made correct observations
•
File modifications: Check if the agent edited config files or wrote expected outputs
•
Service behavior: Verify if the agent's fix actually resolved the issue
What not to check
•
Never check the content of the agent's report/response. The verifier must not read, parse, or score response.md or any other report file the agent writes. Report quality is evaluated entirely by the LLM judge using criteria in rubric.json. If your verifier reads the agent's response, it will break — the report location on the volume differs from the local authoring layout.
•
Don't verify the agent's reasoning or explanation (that's the LLM judge's job)
•
Keep checks binary: passed or not. Partial credit on programmatic checks comes from having multiple checks, not from scoring individual checks partially.
Exit code contract
The verifier must exit non-zero when any programmatic check fails, and exit 0 when all pass. This is enforced by the __main__ block (see example above).

This exit code must satisfy two invariants:

•
Fresh environment → exit non-zero. Running verifier.py against a freshly stood-up environment (before the agent or anyone has applied a fix) must fail. If the verifier passes on a fresh environment, your checks aren't actually verifying that the agent fixed anything — they're testing pre-existing state.
•
After golden solution → exit 0. Running golden_solution.py and then verifier.py must succeed. If the verifier still fails after the golden solution is applied, either the solution is incomplete or the checks are wrong.
Test both invariants locally before submitting. Run setup.sh, then verifier.py (should fail), then apply the golden solution manually, then run verifier.py again (should pass).

Accuracy requirements
The verifier must be accurate — minimize both false positives (passing when the agent didn't do the right thing) and false negatives (failing when the agent actually succeeded). If the LLM judge disagrees with the verifier's result on a given run, that is a signal the verifier needs to be improved. Common causes:

•
False positive: The check is too loose (e.g., checking that any row exists instead of the correct row, or matching a substring that appears in unrelated output).
•
False negative: The check is too brittle (e.g., expecting an exact string when the agent used a valid equivalent, or hard-coding an order that isn't guaranteed).
Write checks to be general enough to accept all valid solutions while still rejecting incorrect ones. For example, if the agent needs to set a config value to 100, check that the value is 100 — don't also check that a comment was added on the same line. If the agent needs to fix a query, verify the query returns correct results rather than checking for an exact SQL string.

When a judge/verifier disagreement is found, update the verifier to handle the case correctly rather than dismissing the disagreement. The goal is for the verifier and judge to converge on the same assessment.

4 golden_response.md
The expert-written ideal response to the prompt. This is the benchmark the judge compares the agent's output against. Write it as if you were the perfect data scientist responding to the stakeholder.

Should include:

•
Summary of the investigation approach
•
Key findings with supporting data
•
Root cause identification with evidence
•
Quantified impact
•
Specific, actionable recommendations
5 golden_solution.py
Runnable script that applies the correct fix against live services in /workspace/. Executed by the pipeline pre-check to validate the verifier constraint: after running golden_solution.py, verifier.py must exit 0. The script runs with workdir="/workspace/" inside the sandbox, so it can modify files, call APIs, restart services, etc. — whatever is needed to make all programmatic checks pass.

6 solution.md
Human-readable walkthrough of the solution. Explains the reasoning, the investigation path, and why certain approaches work. Not read by the judge.

Section 9
Data Generation
If your datapoint uses synthetic data, create generate_data.py at the datapoint root. Runs it with setup.sh.

Requirements
•
Deterministic. Use fixed random seeds. Every run must produce identical data.
•
Standard library only. The sandbox has Python 3 but limited packages. Use random, csv, json, datetime, os, etc. Do not rely on pandas, numpy, or other third-party packages.
•
Write output to _seed_data/ (inside environment/). Your Docker services mount this directory to load the data.
Design tips
•
Generate enough data to hide the signal. If your root cause affects 5% of records, you need hundreds of records minimum so the agent can't spot it by scrolling.
•
Embed the problem in the data generation logic. The bug or pattern you want the agent to find should be a natural consequence of how you generate the data — not a post-hoc annotation.
•
Include realistic noise. Not every anomaly is the root cause. Add legitimate variance, seasonal patterns, and normal outliers.
Section 10
Pre-Submission Checklist
Prompt
•
 2-4 sentences — a short Slack message, not a requirements doc
•
 Does not name specific files, tables, or endpoints
•
 Includes one plausible misdirection
•
 Does not hint at the answer
•
 Context comes from workspace docs, not the prompt itself
Production realism (Section 2.1)
•
 Application services use multiple languages/frameworks (not all Python)
•
 API formats vary across services (REST, gRPC, different conventions)
•
 Application services have realistic internals (proper project structure, config files, logging)
•
 Application services have a README.md where appropriate (what it does, how it fits in, key config)
•
 Data services are _-prefixed and faithfully mock real-world platform APIs
•
 Data service APIs are documented in endpoints.md
•
 Application services have commits spanning multiple services in the git history
•
 Bug-introducing commits blend in with other legitimate changes to the same area
•
 Git history uses patches (environment.patches/), covers only non-_ services
•
 Service depth over quantity — each application service feels like a real codebase
Fairness (Section 2.2)
•
 All evidence needed to reach the root cause is accessible in the environment
•
 Investigation path is discoverable through logical reasoning
•
 No esoteric tool knowledge or lucky guesses required
•
 Every red herring can be ruled out with available data
•
 Rubric doesn't penalize reasonable alternative investigation approaches
•
 Walked through the problem yourself without referencing ground_truth/
Difficulty (Section 2.3)
•
 Target: best agent scores below 30%
•
 10+ distinct non-trivial investigation steps needed
•
 Difficulty comes from analytical depth, not missing information
Infrastructure
•
 docker-compose.yml defines all services with a custom network
•
 setup.sh builds, starts, waits for readiness, and verifies endpoints
•
 setup.sh does not exit until every service is accepting requests (not just started)
•
 setup.sh uses set -euo pipefail and exits non-zero on failure
•
 healthcheck.sh (inside environment/) verifies all services from inside the Docker network
•
 All services are accessible by hostname from within the sandbox
Data environment
•
 3+ data sources with genuine entanglement
•
 Root cause requires cross-referencing multiple sources
•
 At least one red herring with real supporting data
•
 Realistic data formats matching real-world platforms
•
 Sufficient data volume (hundreds+ records)
Data generation
•
 generate_data.py uses fixed random seeds
•
 Uses only Python standard library
•
 Writes to _seed_data/ inside environment/
Ground truth
•
 Majority of points are in programmatic_checks (fix verification), not criteria
•
 Programmatic checks verify the fix was applied and the system improved
•
 rubric.json has specific, unambiguous criteria descriptions
•
 rubric.json max_score equals sum of criteria + programmatic check points
•
 facts.md has all four sections: Root Cause, Red Herrings, Ideal Investigation Path, Key Metrics
•
 verifier.py exports run_programmatic_checks() and runs as __main__
•
 verifier.py handles host resolution (DNS vs localhost fallback)
•
 golden_response.md is a complete, expert-quality response
•
 All programmatic_checks IDs in rubric.json match IDs in verifier.py
End-to-end
•
 Run setup.sh locally and verify all services come up
•
 Run verifier.py against fresh environment — must exit non-zero (fail)
•
 Apply golden solution, then run verifier.py again — must exit 0 (pass)
•
 The root cause is not discoverable from a single data source
•
 Solving the problem requires data science / analytical work (querying, joining, computing metrics) — not just reading code
•
 The agent must both diagnose the problem AND apply a fix
•
 A skilled analyst would need 30+ minutes of investigation
