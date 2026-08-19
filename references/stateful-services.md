# Stateful Services and Infrastructure Dependencies

Read this reference when the service owns mutable durable state, uses SQLite or another local database,
mounts persistent volumes, or deploys infrastructure services beside the application.

## Contents

- [Define state ownership](#define-state-ownership)
- [Manage schemas and migrations](#manage-schemas-and-migrations)
- [Operate SQLite deliberately](#operate-sqlite-deliberately)
- [Back up and restore](#back-up-and-restore)
- [Mount durable storage safely](#mount-durable-storage-safely)
- [Treat infrastructure services as dependencies](#treat-infrastructure-services-as-dependencies)
- [Verify operational contracts](#verify-operational-contracts)

## Define State Ownership

- Inventory every mutable path, database, queue, cache, generated file, and external state owner.
  Classify each as durable, reconstructable, or disposable.
- Keep mutable local state under ignored `data/` by default. Make it disposable from Git's perspective
  but durable from the application's perspective.
- Give each writable path one owning runtime role. Do not let multiple processes or containers write
  the same local database unless the storage engine and filesystem explicitly support that topology.
- Validate the effective path, ownership, free space, and writability before accepting work. Create
  missing directories with narrow permissions.
- Keep caches and derived indexes separate from authoritative state so operators know what can be
  removed safely.

## Manage Schemas and Migrations

- Keep schema changes in ordered, reviewable migrations or another deterministic versioned mechanism.
  Do not bury durable schema mutation in ordinary web startup without an explicit single-owner policy.
- Make migrations idempotent where practical, transactional where supported, and safe to resume after
  interruption.
- Record the current schema version in the database, not only in application code.
- Define compatibility during rolling or interrupted deployment. If old and new binaries cannot share
  a schema, require a controlled stop/migrate/start procedure.
- Test migration from every supported deployed schema and test backup restoration before destructive
  or irreversible changes.

## Operate SQLite Deliberately

- Treat the database file, `-wal`, and `-shm` behavior as one operational contract. Do not copy only the
  main file from a running WAL database as an ad hoc backup.
- Use SQLite's online backup API or `VACUUM INTO` for a consistent live backup. Verify the produced
  database with an integrity check and an application-level smoke query.
- Keep all WAL users on the same host and a compatible local filesystem. Do not place an active WAL
  database on a network filesystem.
- Define busy timeouts and transaction boundaries. Keep write transactions short, serialize writers
  where the application model permits it, and measure lock contention.
- Ensure the directory is writable when SQLite must create or update journal, WAL, or shared-memory
  files, including read-only-container deployments with a writable mounted data directory.
- Plan WAL checkpointing and monitor growth. Do not delete `-wal` or `-shm` files manually while the
  database is active.
- Run integrity checks during controlled maintenance or backup verification, not on every liveness
  probe.

## Back Up and Restore

- Define recovery point and recovery time expectations, backup frequency, retention, encryption, and
  destination before claiming state is durable.
- Keep backups outside the live volume and restrict access at least as tightly as the source.
- Make backup jobs observable without logging backup contents or credentials.
- Test restoration into an isolated location on a schedule. A successful copy is not a verified
  backup until the restored state opens and passes integrity/application checks.
- Document whether shutdown, quiescing, snapshots, or an online API is required for each data store.
- Never make an ordinary `qa`, `clean`, or deployment command delete durable state or backups.

## Mount Durable Storage Safely

- Pre-create the intended mountpoint with narrow ownership in the image when a named volume can inherit
  its metadata. Do not declare Dockerfile `VOLUME`.
- Mount only the paths that must be writable. Keep the root filesystem read-only where the application
  supports it and use a small tmpfs for temporary files.
- Confirm volume lifecycle semantics. An ordinary `docker compose down` should retain named durable
  volumes; destructive `down -v` or prune operations require explicit operator intent.
- Back up before storage migrations, ownership changes, or volume replacement.
- Verify behavior from a clean volume and from a restored existing volume.

## Treat Infrastructure Services as Dependencies

- Inventory databases, log stores, dashboards, proxies, and other vendor services in Compose or the
  deployment platform. Do not treat them as incidental sidecars.
- Use explicitly approved images with reviewed version tags or digests. Do not use mutable `latest`
  for shared environments. If a mirror is supported, document how the mirror maps to the reviewed
  upstream version.
- Give each service a bounded health check, resource expectations, storage path, retention policy,
  authentication boundary, and network exposure.
- Publish only ports required by the host or trusted proxy. Keep unauthenticated internal services on
  internal networks and do not expose them as a convenience.
- Define whether dependency failure affects readiness, liveness, or only an optional capability. Do
  not make application liveness cascade through every observability dependency.
- Keep vendor configuration and secret examples separate from application settings while documenting
  their relationship in the deployment profile.
- Monitor disk use and retention for local log or metrics stores. Do not assume a vendor service will
  automatically delete data based on free disk space.

## Verify Operational Contracts

- Validate application startup with an absent writable directory, a clean volume, an existing schema,
  and a restored backup.
- Exercise migration failure and restart behavior without using production state.
- Verify backup consistency and restore instructions in an isolated environment.
- Validate merged Compose configuration, image versions, network exposure, health checks, volume
  names, and dependency conditions.
- Report any storage engine, filesystem, backup destination, or infrastructure startup that was not
  exercised locally.
