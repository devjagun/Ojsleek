# Odeon Challenge Creation Format

A practical guide to building synthetic investigation challenges that defeat advanced AI reasoning.

---

## Submission Structure

use the challenge title to create the challenge folder

Your challenge folder must contain exactly these directories for upload:

```
your-challenge/
├── environment/                    REQUIRED - The sandbox the agent works in
│   ├── docker-compose.yml          REQUIRED - Service definitions
│   ├── setup.sh                    REQUIRED - Build and start containers
│   ├── healthcheck.sh              REQUIRED - Verify services are ready
│   ├── prompt.md                   REQUIRED - Instructions for the agent
│   ├── endpoints.md                Optional - API reference documentation
│   ├── generate_data.py            REQUIRED if synthetic data - Creates seed data
│   ├── _seed_data/                 Generated data mounted by Docker services
│   ├── service_one/                Application service visible to agent
│   ├── service_two/                Application service visible to agent
│   ├── service_three/              Application service visible to agent
│   └── _hidden_service/            Underscore prefix hides from agent
├── environment.patches/            Optional - Git format-patch files for history
│   ├── 0001-feat-initial.patch
│   └── 0002-fix-something.patch
└── ground_truth/                   REQUIRED - Hidden from agent, used by judge
    ├── rubric.json                 REQUIRED - Scoring schema
    ├── facts.md                    Ground truth for judge
    ├── verifier.py                 Programmatic checks
    ├── golden_response.md          Ideal response
    └── golden_solution.py          Reference solution
```

### Files to Exclude from Upload

Do not include these in your submission zip:

- .git/ directories
- .env files
- __pycache__/ directories
- node_modules/ directories
- .DS_Store files
- Any IDE configuration folders
- Personal notes or draft files

Maximum zip size is five hundred megabytes.

---

## Part One: Foundational Principles

### The Goal

You are creating a self contained data investigation problem. The AI agent receives a vague business complaint, explores live databases and services, analyzes patterns, and must both diagnose the root cause and apply a working fix. Your challenge must be solvable by a skilled human analyst but should cause AI models like Claude Sonnet to fail due to subtle reasoning traps embedded in your custom business logic.

### Three Non Negotiable Requirements

First, production realism. Your environment must feel like a genuine company system. Build services in multiple programming languages. Use Go for one microservice, Python for another, Rust or Node for a third. Each should have its own logging patterns, configuration style, and error handling conventions. Do not create five identical Flask applications.

Second, fairness. A competent data scientist must be able to solve the problem using only information present in the environment. If you cannot walk through your own challenge without referencing your solution files, the challenge is broken.

Third, analytical depth. The problem must require querying databases, joining data across sources, computing metrics, and distinguishing real causes from noise. A problem solvable by reading code alone without touching data is invalid.

---

## Part Two: Creating Original Business Logic

### Invent Your Own Formulas

The challenge must contain formulas, calculations, or business rules that AI has never encountered in training data. Do not use standard financial formulas, common statistical methods, or well known algorithms. Instead, invent domain specific logic that sounds plausible but follows custom rules.

Example of a custom calculation approach:

A logistics company calculates truck route efficiency using a weighted score. The score starts with base miles traveled. Subtract a penalty equal to fifteen percent of miles for each stop after the fourth stop. Add a bonus equal to the cube root of total cargo weight in pounds, but only if the driver rating exceeds four point two. If the route crosses more than two time zones, multiply the entire score by zero point eight seven. Round the intermediate penalty calculation to two decimal places before subtraction, but round the bonus to the nearest whole number before addition.

This formula is entirely invented. AI cannot pattern match to training data because this calculation does not exist anywhere else.

### Layer Multiple Custom Rules

A single custom rule is too easy. Combine at least three interdependent custom rules where earlier calculations feed into later ones. Errors in step one should cascade to produce wrong answers in steps two and three.

Example layered logic:

Step one calculates adjusted inventory value. Take unit cost times quantity. If quantity exceeds reorder threshold, reduce unit cost by the bulk discount rate. Round to four decimal places.

Step two calculates carrying cost. Take adjusted inventory value from step one times annual holding rate divided by three sixty five times days in storage. If days in storage exceeds ninety, apply the extended storage multiplier but only to the portion of days beyond ninety.

Step three calculates total liability. Sum all carrying costs. Apply regional tax rate based on warehouse location. Subtract any prepaid storage credits but cap the subtraction at forty percent of the pre tax total.

Each step depends on the previous step. A rounding error in step one propagates through steps two and three.

---

## Part Three: Embedding AI Failure Traps

Combine multiple traps in each challenge so that one mistake cascades across all outputs. Select three to five traps from the following list and weave them into your custom business logic.

### Trap One: Stateful Row Order Dependency

Design calculations where each row result depends on the computed result from the previous row, not just raw input values. AI models often process rows independently and miss these dependencies.

Implementation: Your loyalty points calculation carries forward unused points from the previous transaction. The current row bonus depends on the accumulated total from all prior rows, not just the current transaction amount.

### Trap Two: Intermediate Rounding

Specify exact precision and rounding stage for intermediate values. State clearly: round the discount percentage to two decimal places before multiplying by subtotal, then truncate the final price to whole cents.

AI models frequently apply rounding only at the final output or apply incorrect precision at intermediate stages.

### Trap Three: Boundary Conditions

Use explicit inclusive versus exclusive boundaries throughout your logic. State whether ranges include or exclude their endpoints. Within thirty days means less than or equal to thirty, not strictly less than thirty. After the cutoff means greater than, not greater than or equal to.

AI models often guess wrong on boundary conditions, especially when rules alternate between inclusive and exclusive within the same challenge.

### Trap Four: Priority Branch Evaluation

Create five or more mutually exclusive conditional branches with strict evaluation order. The first matching condition applies even if later conditions would also match. Document the exact order.

Example: If status is premium and balance exceeds ten thousand, apply rate A. Otherwise if status is premium, apply rate B. Otherwise if balance exceeds ten thousand, apply rate C. Otherwise if account age exceeds five years, apply rate D. Otherwise apply rate E.

An AI that evaluates conditions out of order or fails to short circuit will produce wrong results.

### Trap Five: Conditional Join Strategy

Different record types require different lookup strategies. Exact match for some types, fallback to most recent effective record for others.

Example: Pricing records for domestic orders use exact date match. Pricing records for international orders fall back to the most recent effective date on or before the order date if no exact match exists.

### Trap Six: Context Dependent Null Handling

Null values mean different things in different columns and status contexts. In column A, null means zero. In column B, null means carry forward the previous value. In column C, null means drop the record entirely.

Document these rules in the README but scatter them across multiple sections so the AI must synthesize information from several places.

### Trap Seven: Temporal Alignment

Require alignment across time periods with specific mapping rules. Transactions dated in January through March belong to fiscal quarter four of the previous year. Business days exclude weekends and use a specific regional holiday calendar.

### Trap Eight: Exclusion Rules by Metric Family

Apply different filters depending on which metric is being calculated. Count metrics include all records. Revenue metrics exclude refunded transactions. Ratio metrics exclude both refunded transactions and internal test accounts.

### Trap Nine: Cross Output Consistency

The same threshold or filter must produce consistent behavior across two separate output artifacts. If a customer qualifies for premium in the summary report, they must also appear in the premium customer detail extract using the same qualification logic.

### Trap Ten: Double Cap Constraints

Apply minimum and maximum constraints using two independent caps. The discount cannot exceed twenty percent of subtotal and also cannot exceed fifty dollars. Both caps apply independently. Implementing only one cap fails silently on edge cases.

---

## Part Four: Writing Humanized Prompts and Documentation

### Plain English Only

Write all prompts, READMEs, and documentation in plain conversational English. No mathematical notation. No programming symbols outside of code files. No Greek letters, subscripts, or special characters. Explain everything as you would to a business colleague over coffee.

Bad example: Calculate sigma of returns where sigma equals sqrt of sum of xi minus mu squared divided by n.

Good example: Calculate the spread of daily returns. For each day, find how far the return is from the average. Square that difference. Add up all the squared differences and divide by the number of days. Take the square root of the result.

### Sound Like a Real Person

Your prompt is a message from a frustrated business stakeholder, not a technical specification. Use the kind of language people actually use.

Example prompt:

Something is off with our shipping cost estimates. The logistics team says our quoted rates have been way too low for the past few weeks and we are eating the difference on almost every delivery. They blame it on fuel prices but diesel only went up four percent and our losses are running closer to twenty percent. I pulled some numbers from the rate calculator logs and nothing obvious jumps out. Can you dig into our quoting system and figure out what is actually going wrong here.

This prompt names a problem, provides a plausible but wrong explanation from another team, and gives no specific files or tables to look at.

### Documentation Scatters Clues

Write service READMEs that contain the rules AI needs but spread across multiple sections. Put the rounding specification in the Configuration section. Put the null handling rules in the Data Validation section. Put the boundary conditions in a Troubleshooting section. The AI must read the entire document and synthesize the relevant pieces.

---

## Part Five: Multi Language Challenge Structure

### Technology Stack Requirements

Your challenge must include services written in at least three different programming languages. This requirement exists because real production systems use heterogeneous stacks and because AI models have varying proficiency across languages.

### Standard Language Options

One service in Go. Write your primary API gateway or a performance critical data processor in Go. Include proper go.mod, structured logging, and idiomatic error handling.

One service in Python. Write your analytics pipeline or data transformation layer in Python. Include requirements.txt with pinned versions and standard project structure.

One service in a third language. Choose from Rust, Java, Node.js, or another mainstream language. This service should handle a distinct responsibility like search indexing, message processing, or file generation.

### Legacy Language Options for Maximum Difficulty

To significantly increase challenge difficulty, replace one or more standard language services with legacy or obscure languages. AI models have minimal training data on these languages and will struggle to understand their logic, debug their behavior, or trace bugs through their code.

Fortran. Highly efficient for numerical and scientific computations. Still actively used in high performance computing, financial modeling, and engineering simulations. Use gfortran in Docker. Excellent choice for a calculation engine or batch processing service where the bug involves numerical precision, array indexing, or loop boundary conditions.

Ada. Known for strong typing and reliability focus. Used in aerospace, defense, and safety critical systems. Use GNAT compiler in Docker. Excellent for a validation service or rules engine where the bug involves type conversions, range constraints, or exception handling.

MUMPS or M. Used extensively in healthcare database systems including Epic and VistA. Unique syntax with built in persistence. Use YottaDB or GT.M in Docker. Excellent for a data access layer where the bug involves the unusual variable scoping, implicit array behaviors, or its distinctive control flow.

Forth. Stack based language used in embedded systems for compact size and efficiency. Use gforth in Docker. Excellent for a configuration parser or command processor where the bug involves stack manipulation order, word definitions, or its postfix notation logic.

Factor. Modern stack based language similar to Forth but higher level. Excellent for a transformation service where the bug involves quotation composition, stack shuffling, or combinator behavior.

### Why Legacy Languages Increase Difficulty

AI models trained primarily on modern languages will struggle with these for several reasons.

Syntax unfamiliarity. These languages use conventions that differ dramatically from mainstream languages. Fortran uses column positions. MUMPS uses single character commands. Forth uses postfix notation with explicit stack management.

Limited training data. The volume of code in these languages available for AI training is orders of magnitude smaller than Python or JavaScript. The AI cannot pattern match to familiar idioms.

Different mental models. Stack based languages require thinking about computation differently. MUMPS global variables behave unlike anything in modern languages. Ada constraint checking has no direct equivalent elsewhere.

Cross language debugging. When the agent must trace a bug from a Python service through a Fortran calculation engine and back, the cognitive load multiplies.

### Implementation Guidelines for Legacy Languages

Each legacy language service must be fully functional and Dockerized.

Provide a working Dockerfile that installs the language runtime or compiler. Use official or well maintained base images where available. For Fortran use gcc with gfortran. For Ada use gcc with GNAT. For MUMPS use the YottaDB image. For Forth use gforth.

The service must expose an API that other services can call. Use a thin wrapper if needed. A Python Flask wrapper around a Fortran executable is acceptable. A REST API that shells out to a Forth script is acceptable.

Include a README for the service that describes its purpose and configuration without hinting at the bug. The README should explain the business logic the service implements in plain English.

The bug should live in the legacy language code itself. If you use Fortran for a pricing calculation, the miscalculation should be in the Fortran source not in the Python wrapper.

### Service Interaction Patterns

Services must communicate in production realistic ways. Mix REST, gRPC, and direct database access. Have some services use environment variables for configuration and others use YAML files. Let logging formats differ between services.

---

## Part Six: Verification Files

### Critical Rule: No Comments in Any Submitted Files

All code files you submit must contain zero comments. No inline comments. No docstrings. No explanatory text of any kind within your code files. This applies to verifier.py, generate_data.py, golden_solution.py, service code, and every other file in your submission.

Use clear variable names and logical structure to make code self documenting. Comments give AI hints about what your code does and what the verifier checks. Removing all comments forces the AI to reason about code behavior from structure alone.

### verifier.py Structure

The verifier runs programmatic checks against live services after the agent applies their fix. It must query databases, call APIs, check file contents, and verify the system now behaves correctly.

Required behavior:

Exit with code zero when all checks pass. Exit with nonzero code when any check fails. Return a JSON structure listing each check ID, pass or fail status, points achieved, and a brief detail string.

The verifier must fail on a fresh environment before any fix is applied. The verifier must pass after the golden solution is applied. Test both conditions locally before submitting.

Do not let the verifier read or analyze the agent response file. The verifier checks system state only. Response quality is judged separately.

### verifier.py Dependency Constraints

The verifier runs on the sandbox host which has only the Python standard library available. Do not import psycopg2, requests, pymongo, or any other third party package. This rule is absolute.

To query databases, use subprocess to run docker exec with the database client. For PostgreSQL use docker exec postgres psql with the appropriate flags. For MySQL use docker exec mysql mysql with credentials.

To call HTTP APIs, use subprocess to run curl. Parse the JSON output with the standard json module.

Example database query using subprocess:

```
result = subprocess.run(
    ['docker', 'exec', 'postgres', 'psql', '-U', 'myuser', '-d', 'mydb', '-t', '-A', '-c', 'SELECT COUNT(*) FROM mytable'],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    count = int(result.stdout.strip())
```

Example API call using curl:

```
result = subprocess.run(
    ['curl', '-sf', 'http://localhost:8000/health'],
    capture_output=True,
    text=True
)
if result.returncode == 0:
    data = json.loads(result.stdout)
```

This constraint applies to verifier.py and golden_solution.py. Service code inside Docker containers may use any packages specified in their requirements.txt.

---

## Part Seven: Data Environment Design

### Three Source Minimum

Every challenge requires at least three distinct data sources with genuine entanglement. The root cause must only be discoverable by cross referencing multiple sources. No single table or API reveals the answer.

### Data Entanglement Patterns

Two sources track the same metric but disagree. The agent must determine which is correct and why.

A three way join is required that is not obvious from table names or endpoint documentation.

One source contains a key dimension that must be joined to unlock signal in another source.

### Red Herrings

Include at least one red herring that looks compelling on the surface but falls apart under deeper analysis. The red herring should be a real pattern in the data, not fabricated noise. It should correlate with the symptom but not cause it. Sufficient analysis must be able to rule it out.

Align the red herring with the misdirection mentioned in the prompt. If the prompt says the logistics team blames fuel prices, make fuel prices actually correlate with the problem at first glance before deeper analysis shows the correlation is spurious.

### Realistic Volume

Generate hundreds to thousands of records minimum. The agent must write queries and scripts to analyze the data. If the answer is visible by scrolling through a few dozen rows, the challenge is too easy.

---

## Part Eight: Ground Truth Files

### rubric.json

Allocate the majority of points to programmatic checks, not LLM scored criteria. If something can be verified by querying the database or calling an API, make it a programmatic check.

Criteria descriptions must be specific. Name the exact finding required. Describe what partial credit looks like. Include penalties for common wrong conclusions.

### facts.md

Document the root cause precisely. Name the exact mechanism, the specific parameter, the precise data relationship. List all red herrings with explanations of why they look plausible and how to rule them out. Include a table of key metrics with exact expected values.

### golden_solution.py

A runnable script that applies the correct fix. After running this script, verifier.py must pass. The script modifies files, calls APIs, restarts services, or whatever else is needed to correct the problem.

### golden_response.md

The expert written ideal response. Write it as if you were the perfect data scientist explaining findings to the original stakeholder. Include investigation approach, key findings with data, root cause with evidence, quantified impact, and specific recommendations.

---

## Part Nine: Final Checklist

### Prompt Requirements

Prompt is two to four sentences written like a real Slack message.

Does not name specific files or tables.

Includes one plausible misdirection.

Does not hint at the answer.

### Logic Requirements

Custom logic uses formulas or rules you invented. AI cannot pattern match to training data.

At least three AI failure traps are embedded and cascade into each other.

All documentation is written in plain English with no mathematical notation or special symbols.

### Technical Requirements

Services are written in at least three different programming languages.

Consider using at least one legacy language such as Fortran, Ada, MUMPS, or Forth to increase difficulty.

All submitted code files contain zero comments of any kind. No inline comments. No docstrings.

### Data Requirements

Three or more data sources with genuine entanglement.

At least one red herring with real supporting data.

Hundreds to thousands of records minimum.

### Verification Requirements

Majority of rubric points come from programmatic checks.

Fresh environment causes verifier to fail.

Golden solution causes verifier to pass.

### Fairness Requirements

A skilled human can solve the problem without referencing ground truth files.

All evidence needed to find the root cause exists in the environment.

Every red herring can be ruled out with available data.

### Difficulty Target

Best available AI agent scores below thirty percent.

At least ten distinct non trivial investigation steps needed.

---

## Part Ten: Submission Folder Cleanup

Before creating your upload zip, ensure your challenge folder contains only the required directories.

Keep in the folder:

- environment/ with all required files
- ground_truth/ with all required files
- environment.patches/ if you have git history

Remove from the folder:

- Any personal notes or planning documents
- Draft versions of files
- Test outputs or logs
- IDE configuration files and folders
- Operating system files like .DS_Store
- Cache directories like __pycache__ or node_modules
- Version control directories like .git

Your upload should be a clean zip containing only environment/, ground_truth/, and optionally environment.patches/.

---

## Part Eleven: Lessons Learned from SureHaul Challenge

This section documents critical improvements made to the SureHaul Driver Bonus Overpayment Investigation challenge. Future challenge creators must review these lessons to avoid repeating the same mistakes.

### Lesson One: Specification Documents Must Not Reveal Red Herrings

The original DEBS_Specification.md included an Important Notes section that explicitly stated fuel costs, training, vehicle type, and zone managers do NOT affect bonus calculations. This allowed agents to dismiss all red herrings without any data analysis, trivializing twenty points worth of investigation work.

Fix applied: Remove any documentation that explicitly rules out red herrings. The agent must analyze data to determine what factors are and are not relevant. Red herrings should be dismissible only through actual investigation, not by reading a specification.

Rule for future challenges: Never include statements like "X does not affect Y" in visible documentation. Let the data speak for itself. If a red herring involves fuel costs, the agent should have to query fuel data, correlate it with the problem timeline, and conclude through analysis that correlation does not imply causation.

### Lesson Two: Verifier Must Detect All File Modifications Outside Expected Scope

The original verifier only checked for specific fabrication patterns in the Fortran code such as rating inversion, BPI multiplier changes, and familiarity condition inversion. Agents fabricated bugs by modifying app.py files with SQL query changes, tenure calculation changes, zone filter removal, and GROUP BY additions for non existent duplicates. The verifier passed these because it did not check app.py at all.

Fix applied: Added SHA256 checksums of all files that the golden solution does NOT modify. The verifier now computes current checksums and compares against original values. Any modification to files outside the expected fix scope triggers the fabricated bugs penalty.

Rule for future challenges: The verifier must explicitly check that ONLY the files expected to be modified were actually modified. Store original checksums of all other source files. If an agent modifies working code to fix a bug that does not exist, the verifier must detect and penalize this.

Implementation pattern:

```
original_hashes = {
    "service_one/app.py": "abc123...",
    "service_two/main.go": "def456...",
}

for path, expected in original_hashes.items():
    current = compute_sha256(path)
    if current != expected:
        return False, f"{path} was modified but should not be"
```

### Lesson Three: Rubric Score Totals Must Match

The original rubric had max_score of 100 but criteria summed to 75 and programmatic_checks summed to 40, totaling 115. This mismatch causes validation failures.

Fix applied: Updated max_score to 115 to match actual totals.

Rule for future challenges: Always verify that max_score equals the sum of all criteria points plus all programmatic_check points. Penalties do not count toward the total.

### Lesson Four: Golden Solution String Replacements Must Exactly Match Source

The golden_solution.py used string replacement to fix bugs. If the old_function string does not exactly match the actual file content including whitespace and indentation, the replacement silently fails.

Fix applied: Verified golden_solution.py strings match the actual buggy code character for character.

Rule for future challenges: After writing golden_solution.py, always test the full flow. Reset to buggy state, run golden_solution.py, then run verifier. Both transitions must work. Buggy state must fail verifier. Fixed state must pass verifier.

### Lesson Five: Verifier Checks Must Catch Spirit Violations Not Just Literal Patterns

The original no_fabricated_bugs check looked for specific patterns like rating less than 4.2 or BPI multiplier of 1.15. Agents fabricated entirely different bugs that did not match these patterns, so the check passed despite clear violations.

Fix applied: Expanded the check to detect any modification to files that should not be touched, regardless of what the modification contains.

Rule for future challenges: Design verifier checks to catch the spirit of the requirement, not just specific known patterns. An agent may fabricate a bug you did not anticipate. The safest approach is to verify that only expected files were modified and that modified files contain expected changes.

---

## Part Twelve: Requirements for Future Unique Challenges

Each new Odeon challenge must be substantially different from previous challenges. This section defines what unique means and what must be preserved.

### What Must Be Different

Domain and business context. Do not create another logistics or driver bonus challenge. Choose a completely different industry such as healthcare billing, insurance claims, manufacturing quality control, energy grid management, telecommunications billing, retail inventory, or financial trading.

Data schema. Do not reuse table structures. Invent new entities with different relationships. If the previous challenge had drivers, zones, and shifts, the next might have patients, providers, and claims or instruments, positions, and trades.

Calculation logic. Do not reuse formulas. Invent completely new multi stage calculations with different intermediate steps, different rounding rules, and different conditional branches.

Bug types. Do not repeat the same bugs. If the previous challenge had a boundary condition bug and a priority branch bug, the next might have a temporal alignment bug and a null handling bug.

Red herrings. Do not reuse the same misdirection patterns. Invent new plausible but incorrect theories that require different data analysis to dismiss.

### What Must Be Preserved

Complexity level. New challenges must match or exceed the complexity of SureHaul. This means at minimum three distinct services in different programming languages, at least one legacy or obscure language, multiple database tables requiring joins, multi stage calculations with intermediate values, and at least three embedded AI traps.

Trap density. New challenges must embed three to five traps from the trap catalog in Part Three. Each trap must be woven into the custom business logic, not bolted on as an afterthought.

Investigation depth. New challenges must require the agent to query databases, trace data through multiple services, correlate patterns across time, and distinguish causation from correlation.

Production realism. New challenges must feel like real company systems with heterogeneous technology stacks, different logging patterns, realistic configuration approaches, and believable business context.

### Trap Reuse Guidelines

You may reuse trap types but must implement them differently.

Boundary condition traps must use different thresholds, different value meanings, and different inclusive versus exclusive combinations than previous challenges.

Priority branch traps must have different numbers of branches, different condition types, and different fallback behaviors than previous challenges.

Intermediate rounding traps must use different precision levels, different rounding stages, and different combination with other operations than previous challenges.

### Reference Challenge Complexity Metrics

SureHaul challenge metrics for comparison:

- Three services: Go gateway, Python analytics, Fortran calculation engine
- Eleven database tables
- Three stage calculation: BPI, zone factor, tier rate
- Two embedded bugs: boundary condition, priority branch order
- Four red herrings: fuel costs, training program, vehicle types, zone managers
- Obfuscated variable names in legacy code
- Custom business logic not found in training data

New challenges should target similar or greater metrics across all dimensions.

---

## Part Thirteen: Anti Patterns to Avoid

This section lists specific mistakes to avoid based on real evaluation failures.

### Anti Pattern One: Explicit Exclusion Lists

Do not write documentation that says "The following factors do NOT affect the calculation" followed by a list. This hands the agent the answer for dismissing red herrings.

Instead: Let the data show that factors are uncorrelated. Include the data for red herrings in the database but do not document their irrelevance.

### Anti Pattern Two: Narrow Fabrication Detection

Do not write verifier checks that only catch specific known fabrications. An agent may invent a completely novel fabrication.

Instead: Verify that only expected files were modified and that modifications match expected patterns. Use file checksums for files that should not change.

### Anti Pattern Three: Untested Golden Solutions

Do not submit a golden_solution.py that has not been tested end to end against the actual buggy state.

Instead: Always run the full cycle. Reset to buggy, verify verifier fails, apply golden, verify verifier passes.

### Anti Pattern Four: Mismatched Score Totals

Do not set max_score without adding up all criteria and programmatic_check points.

Instead: Calculate totals explicitly. max_score = sum(criteria points) + sum(programmatic_check points).

### Anti Pattern Five: Comments in Submitted Code

Do not include comments in verifier.py, golden_solution.py, generate_data.py, or service code. Comments leak information about what the code does and what the verifier checks.

Instead: Use clear variable and function names. Let code structure convey intent.

### Anti Pattern Six: Single Point of Failure Traps

Do not embed only one trap that the agent might guess correctly by chance.

Instead: Layer multiple traps so that getting one right but another wrong still produces incorrect results.

### Anti Pattern Seven: Trivially Dismissible Red Herrings

Do not create red herrings that can be dismissed by reading one line of documentation or noticing that a table is not joined anywhere.

Instead: Create red herrings that require querying data, computing correlations, and reasoning about causation versus correlation.

**CRITICAL**
After creation of the challenge run the test and make sure our oracle_solution passes against our verifier.py without hardcoding anything
