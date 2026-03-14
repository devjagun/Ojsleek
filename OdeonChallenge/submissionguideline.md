Back to tasks
New Evaluation Task
Task Details
e.g. ETL Pipeline Debug Task
Brief description of the evaluation scenario...
Create Task

Datapoint Structure Reference
your-task/
├── environment/
│   ├── docker-compose.yml     Service definitions
│   ├── setup.sh               Build & start containers
│   ├── healthcheck.sh         Verify services are ready
│   ├── prompt.md              Instructions for the agent
│   ├── endpoints.md           API reference (optional)
│   └── infrastructure/
│       ├── <service>/         App code (visible to agent)
│       └── _<service>/        Data services (hidden)
├── environment.patches/       git format-patch files (optional)
│   └── 0001-feat-*.patch
└── ground_truth/
    ├── rubric.json            Scoring schema
    ├── facts.md               Ground truth for judge
    ├── verifier.py            Programmatic checks
    ├── golden_response.md     Ideal response
    └── golden_solution.py     Reference solution
environment/
The sandbox the agent works in. Requires docker-compose.yml, setup.sh, healthcheck.sh, and prompt.md. Prefix infrastructure service dirs with underscore to hide from the agent.

ground_truth/
Scoring and verification materials, never shown to the agent. rubric.json is required; other files improve scoring accuracy.

environment.patches/ (optional)
Git format-patch files applied via git am to establish version history. Must apply cleanly in alphabetical order.

Tips: Exclude .git/, .env, __pycache__/, and node_modules/. Max zip size is 500 MB.

Upload Datapoint
Drop your .zip file or folder here

or browse files / browse folder

Must contain environment/, ground_truth/, and optionally environment.patches/