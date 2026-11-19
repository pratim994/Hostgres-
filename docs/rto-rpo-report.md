# RTO / RPO report template

Do not fill in target values as if they were measured. Run the tests and record observed results.

## Environment

- Host CPU/RAM:
- Docker version:
- PostgreSQL image/version:
- Patroni version:
- etcd version:
- HAProxy version:
- Replication mode: asynchronous (V1 default)

## Measurements

| Run | Failure type | Detection (s) | Promotion (s) | First successful app write (s) | Acknowledged transactions lost |
|---:|---|---:|---:|---:|---:|
| 1 | Primary stop | | | | |
| 2 | Primary stop | | | | |
| 3 | Primary stop | | | | |
| 4 | Primary stop | | | | |
| 5 | Primary stop | | | | |

- Median end-to-end RTO:
- Worst observed end-to-end RTO:
- Maximum observed replication lag:
- RPO (lost acknowledged commits):
- Notes / anomalies:

## Method

RTO starts at the recorded primary-stop timestamp and ends at the first successful committed write through HAProxy. RPO is the number/time interval of acknowledged commits absent after recovery, determined by comparing an independent client-side commit log with the recovered table.

State the test limitations. In particular, a single-host Docker deployment does not test host-level availability.
