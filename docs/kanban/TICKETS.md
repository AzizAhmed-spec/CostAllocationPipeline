# FinOps Cost Allocation Pipeline: tickets

Replace Apptio TBM Studio with an in-house cloud cost allocation and chargeback pipeline: Cloudability -> AWS Lambda -> S3 -> Databricks (Bronze/Silver/Gold) -> FOCUS v1.4 output -> API and Power BI, charging back 100% of cloud cost to portfolios and business units.

## Architecture & Discovery

### FIN-1: Define cost group hierarchy and allocation rules

**Status:** Done | **Priority:** High | **Points:** 3

**Depends on:** none

**Description**

Document the five cost groups (Vendor Consumption Costs, Shared Costs at account level, Platform, Portfolio, Application) and the allocation order CSP -> Shared Costs -> Platform -> Portfolio -> Business Unit. This becomes the single source of truth the allocation engine is built against. State the cost neutrality principle: total cost in must equal total cost out after allocation.

**Acceptance criteria**

- [ ] Hierarchy diagram and cost group definitions published in Confluence
- [ ] Each cost group has an owner, a definition and at least one worked example
- [ ] Allocation order is agreed with the FinOps lead and recorded
- [ ] Cost neutrality principle is written down as a testable rule

### FIN-2: Evaluate Databricks vs Snowflake as the analysis platform

**Status:** In Progress | **Priority:** High | **Points:** 5

**Depends on:** none

**Description**

Compare Databricks and Snowflake for this workload: PySpark support, Medallion fit, S3 integration, Power BI connectivity, security model, run cost at expected monthly volume, and operational effort. Produce a recommendation the team can approve and record as an architecture decision.

**Acceptance criteria**

- [ ] Weighted scoring matrix covering cost, PySpark support, S3 and Power BI integration, governance and ops effort
- [ ] One month of FOCUS-shaped data loaded and queried on each platform, or a documented reason a platform was excluded
- [ ] Monthly cost estimate for both options using realistic data volumes
- [ ] Recommendation approved and saved as an architecture decision record in the repo

### FIN-3: Write enterprise architecture blueprint

**Status:** Done | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-1

**Description**

Produce the architecture document covering the Medallion layers, the allocation and chargeback engines, the REST API layer, and the reporting layer. Include data flow, component responsibilities, non-functional requirements and open risks.

**Acceptance criteria**

- [ ] Document covers ingestion, Bronze/Silver/Gold, allocation engine, chargeback engine, API and Power BI layer
- [ ] Data flow diagram shows every system boundary and file or table handoff
- [ ] Non-functional requirements stated: freshness, reconciliation tolerance, availability, access control
- [ ] Reviewed by the tech lead; open risks listed with owners

## Ingestion (Cloudability to S3)

### FIN-7: Lambda: extract Cloudability v3 cost data to S3 as FOCUS CSV

**Status:** In Review | **Priority:** High | **Points:** 8

**Depends on:** FIN-4, FIN-5

**Description**

AWS Lambda that authenticates to the Cloudability v3 reporting API, pulls cost data for AWS, Azure, GCP and OCI, transforms each row to FOCUS v1.4 plus x_ columns, and writes CSV files to the output S3 bucket for Databricks. Failures are isolated per row and per platform so one bad record or platform does not stop the run.

**Acceptance criteria**

- [ ] Writes FOCUS v1.4 CSV with the agreed x_ columns for each of the four platforms
- [ ] Downstream-populated Allocated* columns are written as empty strings
- [ ] Returns HTTP 200 for full success, 207 for partial success and 500 when no rows were processed
- [ ] A bad row or a failing platform is logged with context and skipped without aborting the run
- [ ] Code review approved; endpoint and report parameters confirmed under FIN-9 before production

### FIN-8: Secrets Manager integration and environment configuration

**Status:** In Review | **Priority:** Medium | **Points:** 3

**Depends on:** none

**Description**

Fetch the Cloudability API key from AWS Secrets Manager, supporting both a raw string secret and a JSON-formatted secret. All configuration comes from environment variables: OUTPUT_BUCKET, CLOUDABILITY_SECRET_NAME and CLOUDABILITY_API_BASE.

**Acceptance criteria**

- [ ] Both secret formats are parsed correctly and covered by tests
- [ ] Missing or malformed configuration fails fast with a clear error message
- [ ] No secret value appears in code, logs or error output
- [ ] Lambda execution role grants only the required secret read and bucket write permissions

### FIN-9: Confirm Cloudability report configuration

**Status:** To Do | **Priority:** High | **Points:** 2

**Depends on:** FIN-7

**Description**

Confirm the Cloudability API endpoint URL, dimensions, metrics, tag and category fields, and date range against the actual saved report configuration. Until this is done the Lambda defaults are placeholders and must not be used in production.

**Acceptance criteria**

- [ ] Report definition recorded in the repo and signed off by the Cloudability administrator
- [ ] Lambda parameters match the confirmed report exactly
- [ ] Totals from a pull for one closed month match the Cloudability console within the agreed tolerance
- [ ] Tag and category fields required by FIN-6 are confirmed present in the output

### FIN-10: Pagination, rate limiting and retry handling for the Cloudability API

**Status:** To Do | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-7

**Description**

Make the extractor safe for full-month pulls: follow pagination to the last page, back off on throttling responses, retry transient failures with a bounded policy, and avoid duplicate rows when a retry overlaps a page.

**Acceptance criteria**

- [ ] A full month is retrieved across all pages with row count equal to the API-reported total
- [ ] Throttling and 5xx responses trigger exponential backoff with a retry cap
- [ ] Retries never produce duplicate rows in the output
- [ ] Behaviour covered by tests using mocked API responses

## FOCUS Normalization

### FIN-4: Map Cloudability fields to FOCUS v1.4

**Status:** Done | **Priority:** High | **Points:** 8

**Depends on:** none

**Description**

Build the column-by-column mapping from the Cloudability v3 reporting output to the FOCUS v1.4 schema. Identify gaps where Cloudability does not supply a FOCUS field (for example ResourceId, Tags and SKU-level detail) and record the workaround or accepted limitation for each.

**Acceptance criteria**

- [ ] Every mandatory FOCUS v1.4 column is mapped, derived, or explicitly flagged as a gap
- [ ] Each gap has a documented workaround or an accepted-limitation note
- [ ] Mapping table is versioned in the repo and machine-readable
- [ ] Mapping validated against a real sample export from Cloudability

### FIN-5: Specify custom x_ columns (data dictionary)

**Status:** Done | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-1, FIN-4

**Description**

Define the Scotiabank-specific columns appended to FOCUS: x_ConsumptionType, x_SharedCost_*, x_PlatformId and x_PlatformName, x_PortfolioId and x_PortfolioName, x_ExchangeRate, and the x_BusinessUnit_* family (Department, SVP, VP, DP, Director, Team, Owner, Creator, User, ChargebackCostCenter). Also define the downstream-populated Allocated* columns.

**Acceptance criteria**

- [ ] Data dictionary lists type, nullability, source and derivation rule for every x_ column
- [ ] AllocatedMethodId, AllocatedMethodDetails, AllocatedResourceId, AllocatedResourceName and AllocatedTags are defined as populated by the allocation engine
- [ ] No x_ column collides with a reserved FOCUS name
- [ ] Dictionary reviewed and approved by the FinOps lead

### FIN-6: Derive business unit hierarchy from Cloudability tags

**Status:** In Progress | **Priority:** High | **Points:** 5

**Depends on:** FIN-5

**Description**

Populate the x_BusinessUnit_* fields from Cloudability tags and categories (tag2, tag5, tag8, tag12, tag14, tag15, tag17, tag22, tag23, tag35, category17-19, category22), applying documented fallback rules such as x_VP using tag5 and falling back to category17. Validate every derived value against the master file.

**Acceptance criteria**

- [ ] Precedence and fallback rule documented for every x_BusinessUnit_* field
- [ ] Derived values validated against the master file; mismatches written to an exception output with a reason code
- [ ] Share of cost rows resolving to a business unit is measured and reported (proposed target 95%, to be agreed)
- [ ] Unit tests cover each fallback path and a row with every tag missing

### FIN-11: GCP cost ingestion and FOCUS output via PySpark Medallion

**Status:** In Progress | **Priority:** High | **Points:** 8

**Depends on:** FIN-4, FIN-5

**Description**

Python/PySpark pipeline that takes GCP costs from Cloudability CSV exports through Bronze, Silver, Gold and the FinOps Hub, producing FOCUS-compliant CSVs loaded into Databricks. Developed on branch feat/gcp-cost-allocation.

**Acceptance criteria**

- [ ] Bronze, Silver, Gold and Hub stages run end to end on a real GCP export
- [ ] Output CSV passes the FOCUS schema validator (FIN-15)
- [ ] Row counts and total cost reconcile between source and output
- [ ] Untagged rows are retained and routed to the exception output, not dropped
- [ ] Pull request reviewed and approved

### FIN-12: AWS cost conversion to FOCUS v1.4

**Status:** To Do | **Priority:** High | **Points:** 8

**Depends on:** FIN-4, FIN-5

**Description**

Convert AWS cost rows to FOCUS v1.4, handling amortized commitment discounts (Savings Plans and Reserved Instances), marketplace charges, credits, refunds and tax, and AWS account to portfolio ownership through tags.

**Acceptance criteria**

- [ ] BilledCost, EffectiveCost and ContractedCost follow the FOCUS definitions for commitment discounts
- [ ] Marketplace, credit, refund and tax rows are classified with the correct ChargeCategory
- [ ] Totals reconcile to the Cloudability console for a closed month
- [ ] Output passes the FOCUS schema validator

### FIN-13: Azure cost conversion to FOCUS v1.4

**Status:** Backlog | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-12

**Description**

Convert Azure rows to FOCUS v1.4, mapping subscription and resource group to the account fields, handling reservation amortization and Azure-specific tag casing and inheritance.

**Acceptance criteria**

- [ ] Subscription and resource group map to SubAccountId and SubAccountName per the mapping table
- [ ] Reservation purchases and usage are not double counted
- [ ] Tag keys are matched case-insensitively and normalized
- [ ] Totals reconcile to the Cloudability console for a closed month

### FIN-14: OCI cost conversion to FOCUS v1.4

**Status:** Backlog | **Priority:** Low | **Points:** 5

**Depends on:** FIN-12

**Description**

Convert Oracle Cloud Infrastructure rows to FOCUS v1.4, mapping compartments to the account hierarchy and agreeing how untagged compartments receive an owner.

**Acceptance criteria**

- [ ] Compartment hierarchy maps to the account fields with a documented rule
- [ ] Rows with no owner are flagged and routed to the exception output
- [ ] Totals reconcile to the Cloudability console for a closed month
- [ ] Output passes the FOCUS schema validator

### FIN-15: FOCUS v1.4 schema validator

**Status:** To Do | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-4, FIN-5

**Description**

Reusable validation step that checks any output file for required columns, data types, nullability, allowed values and the x_ column rules, and fails the run with a precise report when a file does not conform.

**Acceptance criteria**

- [ ] Checks column presence, order-independent types, nullability and allowed values for FOCUS and x_ columns
- [ ] A deliberately broken file fails with a message naming the column and row range
- [ ] Runs as a pipeline step and in CI against sample files
- [ ] Validation report is written next to the output

## Databricks Medallion

### FIN-17: S3 landing zone layout, encryption and lifecycle

**Status:** To Do | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-8

**Description**

Define the bucket layout the Lambda writes to and Databricks reads from: prefixes by platform, billing period and run id, server-side encryption, bucket policy, versioning and retention.

**Acceptance criteria**

- [ ] Prefix convention documented and used by the Lambda output
- [ ] Encryption at rest enabled and public access blocked
- [ ] Retention and lifecycle rules defined and applied
- [ ] Reruns for the same period are idempotent and never leave mixed run output

### FIN-18: Bronze layer: raw ingestion into Delta

**Status:** To Do | **Priority:** High | **Points:** 5

**Depends on:** FIN-16, FIN-17

**Description**

Ingest the FOCUS CSVs from S3 into Bronze Delta tables exactly as received, adding ingestion metadata (source file, load timestamp, run id). Bronze is append-only and is never edited.

**Acceptance criteria**

- [ ] Each CSV is loaded once; reprocessing a file does not create duplicates
- [ ] Source file name, load time and run id are stored on every row
- [ ] Malformed rows land in a quarantine table with the parse error
- [ ] Row count in Bronze equals row count in the source files for the period

### FIN-19: Silver layer: cleanse and conform to FOCUS

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-18, FIN-15

**Description**

Standardize types, remove duplicates, align billing periods, apply x_ExchangeRate for currency normalization, and enforce the FOCUS schema. Rows that fail rules go to quarantine with a reason rather than being dropped.

**Acceptance criteria**

- [ ] Silver tables pass the FOCUS schema validator
- [ ] Duplicates are removed deterministically and counted in the run summary
- [ ] Currency conversion uses x_ExchangeRate and is reproducible for a given period
- [ ] Quarantined rows carry a reason code and are included in reconciliation

### FIN-20: Gold layer: allocation-ready cost facts

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-19, FIN-21

**Description**

Join Silver cost rows with the master data (department lookup, platform and portfolio definitions) into a single Gold fact table that has every attribute the allocation engine needs, partitioned by billing period.

**Acceptance criteria**

- [ ] One row per cost line with owner, platform and portfolio attributes attached where known
- [ ] Join misses are counted and listed, not silently dropped
- [ ] Table is partitioned by billing period and performs within the agreed run time
- [ ] Total cost in Gold equals total cost in Silver

## Allocation Engine

### FIN-21: Master data: department lookup and cost center master file

**Status:** To Do | **Priority:** High | **Points:** 5

**Depends on:** FIN-6

**Description**

Own and populate the lookup files the pipeline depends on. department_lookup.csv currently needs manual entries for rows with no tags, the largest being the GCP NetApp Intelligent Services charge shown as Use of cloud-manager-for-cloud. Set up a repeatable way to keep the files current.

**Acceptance criteria**

- [ ] Owner for the Use of cloud-manager-for-cloud charge identified and the row mapped
- [ ] Lookup and master files are versioned in the repo with a documented update process
- [ ] Pipeline reports any cost line whose owner cannot be resolved from the lookup
- [ ] Unassigned cost after lookup is below the agreed threshold

### FIN-22: Direct cost allocation

**Status:** To Do | **Priority:** High | **Points:** 8

**Depends on:** FIN-20, FIN-21

**Description**

Allocate costs of type direct to the owning business unit using the tags the cloud resource carries. Allocation tags come from client_chargeback_centre, resource_client_chargeback_cost_center, project_id, application_id, resource_project_id and user_id, and are written to AllocatedTags.

**Acceptance criteria**

- [ ] Direct rows are assigned using the documented tag precedence
- [ ] AllocatedTags records which tags were used for each row
- [ ] Rows with no usable tag are routed to the exception output
- [ ] Direct total before allocation equals direct total after allocation

### FIN-23: Shared cost allocation (cost follows cost)

**Status:** Backlog | **Priority:** High | **Points:** 8

**Depends on:** FIN-22

**Description**

Distribute account-level shared costs across consuming accounts in proportion to each account's share of total measured usage for the billing period. Populate the x_SharedCost_* columns so the calculation can be audited.

**Acceptance criteria**

- [ ] Shares for a period sum to exactly 100 percent
- [ ] x_SharedCost_* columns store the pool, the basis and the share applied
- [ ] A period with zero measured usage is handled by a documented rule
- [ ] Rounding remainder is assigned deterministically so totals still tie out

### FIN-24: Proportional consumption types (propaws, propres, propgcp, propedp, propazure)

**Status:** Backlog | **Priority:** Medium | **Points:** 8

**Depends on:** FIN-23

**Description**

Implement the proportional allocation methods for each consumption type. Each type spreads its cost pool using its own driver, and the method used is recorded in AllocatedMethodId and AllocatedMethodDetails.

**Acceptance criteria**

- [ ] Each of the five types has a documented driver and is implemented
- [ ] AllocatedMethodId and AllocatedMethodDetails identify the method on every allocated row
- [ ] Each type's pool total is unchanged by allocation
- [ ] Unit tests cover each type with a small worked example

### FIN-25: Platform and portfolio allocation

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-24

**Description**

Assign x_PlatformId and x_PlatformName and x_PortfolioId and x_PortfolioName, then roll platform costs down to the portfolios that consume the platform, following the hierarchy from FIN-1.

**Acceptance criteria**

- [ ] Every cost row carries a platform or an explicit none, and a portfolio
- [ ] Platform cost is fully distributed to portfolios with no remainder
- [ ] Portfolio totals can be traced back to platform and shared cost components
- [ ] Output matches the hand-calculated example agreed with the FinOps lead

### FIN-26: Business unit chargeback rollup

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-25

**Description**

Roll portfolio costs to business units and populate x_BusinessUnit_* including ChargebackCostCenter, producing the final chargeback records for every portfolio.

**Acceptance criteria**

- [ ] Every portfolio has chargeback lines to a cost center
- [ ] Chargeback records carry the full x_BusinessUnit_* hierarchy
- [ ] Business unit totals equal portfolio totals for the period
- [ ] Output is available at month-to-date and month-end grain

### FIN-27: Allocation lineage: method id and Cloudability tag33 mapping

**Status:** Backlog | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-22

**Description**

Map AllocatedMethodId to the Cloudability tag33 values so each allocation can be traced to its method, and populate AllocatedResourceId and AllocatedResourceName where the original resource is known.

**Acceptance criteria**

- [ ] Mapping from tag33 values to method ids is documented and tested
- [ ] Unknown tag33 values are reported and not defaulted silently
- [ ] AllocatedResourceId and AllocatedResourceName are populated when the source resource is known
- [ ] An auditor can follow any chargeback line back to its source rows

### FIN-29: Unallocated and untagged cost exception report

**Status:** Backlog | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-22

**Description**

Report listing cost that could not be allocated or lacks required tags, ranked by amount with the account, service and suggested owner, so the largest gaps are fixed first.

**Acceptance criteria**

- [ ] Report lists unallocated cost by amount with account, service and reason code
- [ ] Trend of unallocated percentage per month is available
- [ ] Report is produced automatically each run
- [ ] Owners can use it to fix tags or lookup entries and see the effect on the next run

## API & Reporting

### FIN-30: REST API: raw and shared cost queries

**Status:** Backlog | **Priority:** Medium | **Points:** 8

**Depends on:** FIN-20, FIN-23

**Description**

Implement POST /api/raw/query to return unallocated source records and POST /api/shared/query to return allocated shared-cost records, with filtering by billing period, platform, account and portfolio.

**Acceptance criteria**

- [ ] Both endpoints accept filters in the request body and return FOCUS-shaped records
- [ ] Large results are paginated
- [ ] Invalid filters return a clear 400 response
- [ ] Endpoints require authentication and are covered by integration tests

### FIN-31: REST API: platforms and portfolios

**Status:** Backlog | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-25

**Description**

Implement GET /api/platforms, GET /api/platforms/{platformId}, GET /api/portfolios and GET /api/portfolios/{portfolioId}, returning allocated totals and cost components.

**Acceptance criteria**

- [ ] List and detail endpoints return consistent shapes
- [ ] Unknown ids return 404
- [ ] Totals match the Gold and chargeback tables for the same period
- [ ] Endpoints are authenticated and tested

### FIN-32: REST API: month-to-date and previous-month file exports

**Status:** Backlog | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-26

**Description**

Implement GET /api/files/month-to-date and GET /api/files/previous-month, returning the final FOCUS CSV for the requested period.

**Acceptance criteria**

- [ ] Month-to-date file refreshes on each pipeline run
- [ ] Previous-month file is frozen once the month is closed and signed off
- [ ] Files pass the FOCUS schema validator
- [ ] Access is limited to authorized consumers

### FIN-33: Power BI semantic model and chargeback reports

**Status:** Backlog | **Priority:** High | **Points:** 8

**Depends on:** FIN-26

**Description**

Build the reporting layer on the final chargeback data: a semantic model and reports by business unit, portfolio, platform and application, with drill-through from chargeback line to source cost.

**Acceptance criteria**

- [ ] Report totals equal the chargeback table totals for the period
- [ ] Users can drill from business unit to portfolio to platform to application
- [ ] Month-to-date and closed-month views are both available
- [ ] Row-level security limits each owner to their portfolios
- [ ] Refresh runs after each successful pipeline run

## Platform & Operations

### FIN-16: Unblock Databricks network egress (firewall whitelist)

**Status:** To Do | **Priority:** High | **Points:** 3 | **Blocked:** Waiting on firewall and networking meeting

**Depends on:** none

**Description**

Databricks workspace finops-rnd-prod needs outbound HTTPS to the GCP APIs, Cloudability and GitHub. Hold the firewall and networking meeting, raise the requests, and prove connectivity from a cluster.

**Acceptance criteria**

- [ ] Meeting held and a request raised with the network team for each required endpoint
- [ ] Allowed endpoints listed in the repo docs with the business justification
- [ ] A test notebook succeeds against each endpoint from a cluster in finops-rnd-prod
- [ ] No broader egress than the approved list is requested

### FIN-34: Orchestration and scheduling

**Status:** Backlog | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-18, FIN-7

**Description**

Schedule the Lambda extraction and the Databricks workflow in order: daily month-to-date runs and a month-end close run, with dependencies so Databricks only starts after the files have landed.

**Acceptance criteria**

- [ ] Lambda schedule and Databricks workflow run in the correct order
- [ ] A failed upstream step prevents downstream steps from running
- [ ] Month-end close can be re-run for a past period without side effects
- [ ] Schedule and run order are documented

### FIN-35: Monitoring, logging and alerting

**Status:** Backlog | **Priority:** Medium | **Points:** 5

**Depends on:** FIN-34

**Description**

Structured logs and alerts for every stage, including an alert on Lambda 207 partial-success results, schema validation failures, reconciliation breaches and runs that did not finish by the expected time.

**Acceptance criteria**

- [ ] Every stage logs row counts, duration and a run id
- [ ] Alerts fire for 207 and 500 results, validation failures and reconciliation breaches
- [ ] An alert contains enough context to find the failing platform or file
- [ ] Alerts are tested once by forcing a failure

### FIN-36: CI/CD, automated tests and code review workflow

**Status:** To Do | **Priority:** Medium | **Points:** 5

**Depends on:** none

**Description**

Set up automated tests and linting that run on every pull request, a branch and review process, and a repeatable deployment for the Lambda and the Databricks code.

**Acceptance criteria**

- [ ] Pull requests run linting and unit tests automatically and must pass before merge
- [ ] Sample FOCUS files are used for regression tests of the transforms
- [ ] Deployment of Lambda and Databricks code is scripted and repeatable
- [ ] Branch and review rules are written in the repo README

### FIN-37: Access control and data governance

**Status:** Backlog | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-18

**Description**

Define who can read raw cost data, who can run the pipeline, and who can see chargeback data per portfolio. Apply the rules in Databricks, S3, the API and Power BI.

**Acceptance criteria**

- [ ] Roles defined for engineers, FinOps analysts and portfolio owners
- [ ] Databricks table access and S3 policies reflect the roles
- [ ] API and Power BI enforce the same visibility rules
- [ ] Access review procedure documented

## Validation & Cutover

### FIN-28: Cost neutrality reconciliation

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-20, FIN-26

**Description**

Automated checks that total cost in equals total cost out at every stage: source to Bronze, Bronze to Silver, Silver to Gold, and Gold to final chargeback. A breach stops publication of the period.

**Acceptance criteria**

- [ ] Check runs after every stage and compares totals by platform and billing period
- [ ] Tolerance is explicit (target zero after rounding) and configurable
- [ ] A breach fails the run and publishes nothing downstream
- [ ] Reconciliation summary is stored with the run for audit

### FIN-38: Parallel run and reconciliation against Apptio TBM Studio

**Status:** Backlog | **Priority:** High | **Points:** 8

**Depends on:** FIN-28, FIN-33

**Description**

Run the new pipeline alongside Apptio TBM Studio for at least two closed months and explain every material variance by portfolio and business unit.

**Acceptance criteria**

- [ ] Two closed months compared at portfolio and business unit level
- [ ] Every variance above the agreed threshold has a documented cause
- [ ] Defects found are fixed or accepted by the FinOps lead
- [ ] Final variance report approved

### FIN-39: Documentation and runbooks

**Status:** Backlog | **Priority:** Medium | **Points:** 3

**Depends on:** FIN-34

**Description**

Write the operator and developer documentation: architecture overview, how to run and re-run a period, how to add a platform, how to update lookup files, and how to respond to each alert.

**Acceptance criteria**

- [ ] README explains the project, setup and how to run each stage
- [ ] Runbook covers month-end close, rerun, rollback and every alert
- [ ] Instructions for updating lookup and master files are included
- [ ] A new team member follows the docs to run a sample period

### FIN-40: User acceptance testing and Apptio cutover

**Status:** Backlog | **Priority:** High | **Points:** 5

**Depends on:** FIN-38, FIN-39

**Description**

Walk portfolio owners through their chargeback numbers, collect sign-off, switch chargeback reporting to the new pipeline, and plan the retirement of Apptio TBM Studio.

**Acceptance criteria**

- [ ] Portfolio owners review and sign off their chargeback numbers
- [ ] Cutover date and rollback plan agreed
- [ ] First production month-end close completed on the new pipeline
- [ ] Apptio decommission plan documented with the date and owner
