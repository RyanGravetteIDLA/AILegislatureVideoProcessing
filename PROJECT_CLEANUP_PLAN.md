# Project Cleanup Plan

This document outlines a comprehensive plan to clean up and improve the Idaho Legislature Media Portal project. It addresses code quality, architecture, deployment processes, and documentation.

## 1. File Structure Cleanup

### High Priority

- [ ] **Remove Deprecated Google Drive Files**
  - `scripts/list_drive_folders.py`
  - `scripts/manage_drive_service.py`
  - `scripts/upload_media_to_drive.py`
  - `src/drive_storage.py`

- [ ] **Consolidate Deployment Scripts**
  - Keep only `deploy_cloud_run.sh` and `deploy_function.sh` 
  - Remove redundant scripts: `deploy_to_cloud_run.sh`, `deploy_cloud_build.sh`, `deploy_main_api.sh`, `deploy_test_api.sh`
  - Update references in documentation

- [ ] **Standardize Database Implementations**
  - Select `transcript_db_firestore.py` as the primary implementation
  - Mark `transcript_db_sqlite.py` and `transcript_db_firebase.py` as deprecated or remove
  - Update all imports to use the selected implementation

### Medium Priority

- [ ] **Organize Documentation**
  - Merge redundant files into a single comprehensive README
  - Create a clear deployment guide that refers to specific scripts
  - Update architecture documentation for microservices

- [ ] **Standardize File Naming**
  - Rename inconsistently named files to follow a single convention
  - Update all imports and references

## 2. Code Quality Improvements

### High Priority

- [ ] **Update Dependencies**
  - Update `requirements.txt` to include all required packages with current versions:
    ```
    flask==2.3.3
    werkzeug==2.3.7
    google-cloud-firestore==2.13.0
    fastapi==0.110.0
    uvicorn==0.28.0
    pydantic==2.6.0
    python-dotenv==1.0.1
    requests==2.31.0
    ```
  - Remove unused dependencies

- [ ] **Fix Security Issues**
  - Remove hardcoded credentials and paths
  - Use environment variables for sensitive information
  - Remove debug logging from production code

### Medium Priority

- [ ] **Improve Error Handling**
  - Replace generic exception handlers with specific ones
  - Add input validation to critical functions
  - Implement consistent error reporting

- [ ] **Refactor Redundant Code**
  - Create utility functions for common operations
  - Extract duplicate methods into shared modules
  - Standardize function naming conventions

### Low Priority

- [ ] **Apply Consistent Formatting**
  - Run Black formatter on all Python code
  - Run ESLint on JavaScript code
  - Add docstrings to undocumented functions

## 3. Deployment Process Improvements

### High Priority

- [ ] **Update Dockerfile**
  - Use a multi-stage build to reduce final image size
  - Update base image to Python 3.11
  - Include all required dependencies
  - Replace `src/minimal_api.py` with the proper Cloud Function handler

- [ ] **Fix Cloud Function Configuration**
  - Update main.py to properly initialize the Firebase app
  - Implement correct API handler function
  - Fix environment variables

### Medium Priority

- [ ] **Improve CI/CD Process**
  - Create GitHub Actions workflow for automated testing
  - Add deployment verification steps
  - Implement rollback capability

- [ ] **Update Docker Compose**
  - Fix incorrect volume mappings
  - Update health check commands
  - Add proper dependency management

## 4. Architecture Improvements

### High Priority

- [ ] **Complete Microservices Migration**
  - Finish implementation of all planned microservices
  - Update documentation to reflect the new architecture
  - Add proper service discovery

### Medium Priority

- [ ] **Standardize API Patterns**
  - Implement consistent response formats
  - Add proper API versioning
  - Document all endpoints with OpenAPI

- [ ] **Improve Data Management**
  - Implement proper pagination for all list endpoints
  - Add caching for frequently accessed data
  - Optimize Firestore queries

## 5. Testing Improvements

### High Priority

- [ ] **Update Existing Tests**
  - Fix broken tests after architecture changes
  - Update test configuration

### Medium Priority

- [ ] **Expand Test Coverage**
  - Add unit tests for all microservices
  - Implement integration tests for API endpoints
  - Add frontend component tests

## 6. Documentation Improvements

### High Priority

- [ ] **Update Main README**
  - Reflect current architecture
  - Update installation and deployment instructions
  - Add troubleshooting section

### Medium Priority

- [ ] **Improve Code Documentation**
  - Add docstrings to all functions
  - Document complex algorithms
  - Add architecture diagrams

## Implementation Tracking

When working on this cleanup plan:

1. Check off items as they are completed
2. Add notes about any issues encountered
3. Update dependencies and file lists as they change
4. Commit changes regularly with descriptive messages

## References

- [Microservices Architecture Plan](MICROSERVICES_ARCHITECTURE_PLAN.md)
- [Cloud Run Deployment Fix](CLOUD_RUN_DEPLOYMENT_FIX.md)
- [CLAUDE.md Configuration](CLAUDE.md)