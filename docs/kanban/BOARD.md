# FinOps Cost Allocation Pipeline: board

40 tickets, 207 story points, 19 points done. Full descriptions and acceptance criteria are in [TICKETS.md](TICKETS.md). Open [index.html](index.html) in a browser for the interactive board.

| Backlog (21) | To Do (10) | In Progress (3) | In Review (2) | Done (4) |
| --- | --- | --- | --- | --- |
| **FIN-13** Azure cost conversion to FOCUS v1.4 [5] | **FIN-9** Confirm Cloudability report configuration [2] | **FIN-2** Evaluate Databricks vs Snowflake as the analysis platform [5] | **FIN-7** Lambda: extract Cloudability v3 cost data to S3 as FOCUS CSV [8] | **FIN-1** Define cost group hierarchy and allocation rules [3] |
| **FIN-14** OCI cost conversion to FOCUS v1.4 [5] | **FIN-10** Pagination, rate limiting and retry handling for the Cloudability API [5] | **FIN-6** Derive business unit hierarchy from Cloudability tags [5] | **FIN-8** Secrets Manager integration and environment configuration [3] | **FIN-3** Write enterprise architecture blueprint [5] |
| **FIN-19** Silver layer: cleanse and conform to FOCUS [5] | **FIN-12** AWS cost conversion to FOCUS v1.4 [8] | **FIN-11** GCP cost ingestion and FOCUS output via PySpark Medallion [8] |   | **FIN-4** Map Cloudability fields to FOCUS v1.4 [8] |
| **FIN-20** Gold layer: allocation-ready cost facts [5] | **FIN-15** FOCUS v1.4 schema validator [3] |   |   | **FIN-5** Specify custom x_ columns (data dictionary) [3] |
| **FIN-23** Shared cost allocation (cost follows cost) [8] | **FIN-16** Unblock Databricks network egress (firewall whitelist) [3] (blocked) |   |   |   |
| **FIN-24** Proportional consumption types (propaws, propres, propgcp, propedp, propazure) [8] | **FIN-17** S3 landing zone layout, encryption and lifecycle [3] |   |   |   |
| **FIN-25** Platform and portfolio allocation [5] | **FIN-18** Bronze layer: raw ingestion into Delta [5] |   |   |   |
| **FIN-26** Business unit chargeback rollup [5] | **FIN-21** Master data: department lookup and cost center master file [5] |   |   |   |
| **FIN-27** Allocation lineage: method id and Cloudability tag33 mapping [3] | **FIN-22** Direct cost allocation [8] |   |   |   |
| **FIN-28** Cost neutrality reconciliation [5] | **FIN-36** CI/CD, automated tests and code review workflow [5] |   |   |   |
| **FIN-29** Unallocated and untagged cost exception report [5] |   |   |   |   |
| **FIN-30** REST API: raw and shared cost queries [8] |   |   |   |   |
| **FIN-31** REST API: platforms and portfolios [5] |   |   |   |   |
| **FIN-32** REST API: month-to-date and previous-month file exports [3] |   |   |   |   |
| **FIN-33** Power BI semantic model and chargeback reports [8] |   |   |   |   |
| **FIN-34** Orchestration and scheduling [5] |   |   |   |   |
| **FIN-35** Monitoring, logging and alerting [5] |   |   |   |   |
| **FIN-37** Access control and data governance [3] |   |   |   |   |
| **FIN-38** Parallel run and reconciliation against Apptio TBM Studio [8] |   |   |   |   |
| **FIN-39** Documentation and runbooks [3] |   |   |   |   |
| **FIN-40** User acceptance testing and Apptio cutover [5] |   |   |   |   |

Numbers in square brackets are story points.
