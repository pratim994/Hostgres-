# Disaster recovery

The current deployment can recover from some container/process failures while etcd retains quorum. It cannot recover from host loss, accidental table deletion, corrupted volumes, or loss of the Compose host. Named volumes are local persistence, not independent backups.

For a real DR workflow, keep encrypted base backups and WAL outside the database host and failure domain, monitor archive freshness, test restore into an isolated environment, and document a recovery target and credential retrieval process. Before promoting or restoring after a site incident, fence the old primary to prevent it from accepting writes. This repo does not yet automate fencing or PITR.
