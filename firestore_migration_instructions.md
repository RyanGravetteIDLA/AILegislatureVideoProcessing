# Firestore Migration Instructions

This guide outlines the steps to migrate from SQLite to Firestore in the Idaho Legislature Media Portal application.

## Background

The application initially used SQLite for local data storage, but we have now migrated to Firestore for improved scalability, cloud-native integration, and better collaboration. This migration was necessary to support the deployment to Google Cloud Run and integration with Firebase Hosting.

## Completed Changes

1. Created a Firestore database in the GCP project `legislativevideoreviewswithai`
2. Implemented a new API module (`api_firestore.py`) that uses Firestore
3. Updated the server module to use the Firestore API by default
4. Created a compatibility layer (`transcript_db_firestore.py`) to support scripts that use the SQLite interface

## Remaining Tasks

1. Run the Firestore migration script to copy data from SQLite to Firestore
2. Update scripts that directly use `transcript_db` to use the Firestore version

## How to Migrate Data from SQLite to Firestore

1. Ensure you have set up Firebase authentication:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials/legislativevideoreviewswithai-80ed70b021b5.json"
```

2. Run the migration script:

```bash
python src/firestore_migration.py --limit 10 --dry-run
```

3. If the dry run looks good, run the actual migration:

```bash
python src/firestore_migration.py
```

4. Validate the migration:

```bash
python src/firestore_migration.py --validate
```

## How Scripts Work with Both Databases

We've implemented a compatibility layer that allows scripts to continue using the `transcript_db` interface while actually using Firestore for storage. This is done through a module called `transcript_db_firestore.py` that implements the same interface but uses Firestore under the hood.

When the server starts, it:
1. Backs up the SQLite implementation to `transcript_db_sqlite.py` (if not already done)
2. Replaces `transcript_db.py` with the Firestore implementation

This allows existing scripts to keep working without code changes.

## Troubleshooting

If you encounter issues with the migration:

1. Check that the Firestore database is accessible:
```bash
python -c "from google.cloud import firestore; db = firestore.Client(project='legislativevideoreviewswithai'); print('Connected to Firestore')"
```

2. Verify your credentials are correctly set up:
```bash
python src/secrets_manager.py test --service-accounts
```

3. If scripts are failing, you can temporarily revert to SQLite by:
```bash
cp src/transcript_db_sqlite.py src/transcript_db.py
```

4. Check the logs in the `data/logs` directory for detailed error messages.

## Architecture

The application now has two parallel API implementations:
- `api.py`: Updated to use Firestore but maintains compatibility with the original design
- `api_firestore.py`: Modern implementation designed specifically for Firestore

The server uses `api_firestore.py` by default, which is optimized for Firestore and adds new features like proper collection organization and Cloud Storage integration.

All data is stored in Firestore collections:
- `videos`: Video files 
- `audio`: Audio files
- `transcripts`: Transcript files
- `other`: Other media files

Each document contains the same fields as the SQLite database plus additional Firestore-specific fields for better integration with GCP services.