# Point-in-time recovery status

PITR is not implemented in the current repository state. PostgreSQL streaming replication and persistent Compose volumes do not provide historical recovery. There is no configured `archive_command`, WAL archive repository, base-backup schedule, retention policy, isolated restore service, or recovery verifier. Do not use the lab to claim backup coverage.

A production implementation should select pgBackRest, configure a remote repository and encrypted credentials, archive WAL continuously, take scheduled full/differential backups, run `check` and restore verification, and restore into an isolated data directory/container. The drill should use a recorded UTC target before a deliberate drop and verify both expected rows and the absence of post-target effects. Never restore over the active primary.
