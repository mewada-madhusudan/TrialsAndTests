# Workflow Tool Database - Mermaid ER Diagram

## Entity Relationship Diagram (Mermaid Format)

```mermaid
erDiagram
    %% Core User Management Entities
    USERS {
        uuid user_id PK "Primary Key"
        varchar username UK "Unique username"
        varchar email UK "Unique email"
        varchar first_name "First name"
        varchar last_name "Last name"
        boolean is_active "Active status"
        timestamp created_at "Creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    ROLES {
        uuid role_id PK "Primary Key"
        varchar role_name UK "Unique role name"
        text role_description "Role description"
        timestamp created_at "Creation timestamp"
    }

    USER_ROLES {
        uuid user_role_id PK "Primary Key"
        uuid user_id FK "Foreign key to users"
        uuid role_id FK "Foreign key to roles"
        varchar area_id "Area assignment for role"
        boolean is_active "Active assignment status"
        timestamp assigned_at "Assignment timestamp"
    }

    %% Quarter and Upload Management
    QUARTERS {
        uuid quarter_id PK "Primary Key"
        varchar quarter_name UK "Unique quarter name (Q1 2024)"
        integer year "Year"
        integer quarter_number "Quarter number (1-4)"
        date start_date "Quarter start date"
        date end_date "Quarter end date"
        boolean is_active "Active status"
        timestamp created_at "Creation timestamp"
    }

    DATA_UPLOADS {
        uuid upload_id PK "Primary Key"
        uuid quarter_id FK "Foreign key to quarters"
        uuid uploaded_by FK "Foreign key to users (Process Owner)"
        varchar file_name "Uploaded file name"
        text file_path "File storage path"
        bigint file_size "File size in bytes"
        varchar upload_status "processing/completed/failed"
        integer records_count "Number of records in upload"
        timestamp uploaded_at "Upload timestamp"
        timestamp processed_at "Processing completion timestamp"
    }

    %% Core Workflow Entity
    WORKFLOW_RECORDS {
        uuid record_id PK "Primary Key"
        uuid upload_id FK "Foreign key to data_uploads"
        uuid quarter_id FK "Foreign key to quarters"
        uuid area_owner_id FK "Foreign key to users (Area Owner)"
        uuid certifier_id FK "Foreign key to users (Certifier)"
        varchar record_reference "Business record reference"
        varchar area_code "Area/department code"
        varchar business_unit "Business unit name"
        decimal amount "Monetary amount"
        varchar currency "Currency code (USD, EUR, etc.)"
        text description "Record description"
        varchar process_owner_status "pending_review/pending_certification/certified/reopened"
        varchar area_owner_status "pending_confirmation/confirmed/reopened"
        varchar certifier_status "pending_review/certified/reopened"
        varchar overall_status "in_progress/certified/reopened"
        timestamp created_at "Creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    %% Audit and History Tracking
    STATUS_HISTORY {
        uuid history_id PK "Primary Key"
        uuid record_id FK "Foreign key to workflow_records"
        uuid user_id FK "Foreign key to users"
        varchar persona_type "process_owner/area_owner/certifier"
        varchar previous_status "Previous status value"
        varchar new_status "New status value"
        varchar action_type "status_change/comment_added/file_upload/assignment"
        timestamp created_at "Action timestamp"
    }

    COMMENTS {
        uuid comment_id PK "Primary Key"
        uuid record_id FK "Foreign key to workflow_records"
        uuid user_id FK "Foreign key to users"
        uuid parent_comment_id FK "Self-reference for threading"
        varchar persona_type "process_owner/area_owner/certifier"
        text comment_text "Comment content"
        boolean is_internal "Internal note vs external comment"
        timestamp created_at "Creation timestamp"
        timestamp updated_at "Last update timestamp"
        boolean is_deleted "Soft delete flag"
    }

    PREVIOUS_QUARTER_REFERENCES {
        uuid reference_id PK "Primary Key"
        uuid current_record_id FK "Foreign key to current quarter record"
        uuid previous_record_id FK "Foreign key to previous quarter record"
        jsonb match_criteria "Matching criteria used"
        decimal confidence_score "Match confidence (0.00-1.00)"
        timestamp created_at "Creation timestamp"
    }

    AUDIT_TRAIL {
        uuid audit_id PK "Primary Key"
        uuid user_id FK "Foreign key to users"
        varchar session_id "User session identifier"
        inet ip_address "User IP address"
        varchar action_type "Type of action performed"
        varchar table_name "Database table affected"
        uuid record_id "Record identifier affected"
        jsonb old_values "Previous values (JSON)"
        jsonb new_values "New values (JSON)"
        text action_description "Human-readable action description"
        timestamp created_at "Action timestamp"
        text user_agent "User browser/client info"
    }

    %% Relationships - User Management
    USERS ||--o{ USER_ROLES : "has roles"
    ROLES ||--o{ USER_ROLES : "assigned to users"
    
    %% Relationships - Data Upload Flow
    USERS ||--o{ DATA_UPLOADS : "uploads files (Process Owner)"
    QUARTERS ||--o{ DATA_UPLOADS : "contains uploads"
    DATA_UPLOADS ||--o{ WORKFLOW_RECORDS : "contains records"
    QUARTERS ||--o{ WORKFLOW_RECORDS : "has records"
    
    %% Relationships - Workflow Assignments
    USERS ||--o{ WORKFLOW_RECORDS : "assigned as area_owner"
    USERS ||--o{ WORKFLOW_RECORDS : "assigned as certifier"
    
    %% Relationships - Status and Comments
    WORKFLOW_RECORDS ||--o{ STATUS_HISTORY : "has status changes"
    USERS ||--o{ STATUS_HISTORY : "performs actions"
    WORKFLOW_RECORDS ||--o{ COMMENTS : "has comments"
    USERS ||--o{ COMMENTS : "makes comments"
    COMMENTS ||--o{ COMMENTS : "has replies (threading)"
    
    %% Relationships - Historical References
    WORKFLOW_RECORDS ||--o{ PREVIOUS_QUARTER_REFERENCES : "current quarter record"
    WORKFLOW_RECORDS ||--o{ PREVIOUS_QUARTER_REFERENCES : "previous quarter record"
    
    %% Relationships - Audit Trail
    USERS ||--o{ AUDIT_TRAIL : "generates audit entries"
```

## Workflow State Diagram

```mermaid
stateDiagram-v2
    [*] --> FileUpload : Process Owner uploads quarterly file
    
    FileUpload --> InitialState : File processed successfully
    
    state InitialState {
        ProcessOwner_PendingReview
        AreaOwner_PendingConfirmation
        Certifier_PendingReview
    }
    
    InitialState --> AreaOwnerAction : Area Owner reviews and updates
    
    state AreaOwnerAction {
        AreaOwner_Confirmed
        ProcessOwner_PendingCertification
        Certifier_PendingReview
    }
    
    AreaOwnerAction --> CertifierDecision : Certifier reviews
    
    state CertifierDecision {
        [*] --> Certified : Certifier approves
        [*] --> Reopened : Certifier rejects
    }
    
    state Certified {
        ProcessOwner_Certified
        AreaOwner_Confirmed
        Certifier_Certified
        OverallStatus_Certified
    }
    
    state Reopened {
        ProcessOwner_Reopened
        AreaOwner_Reopened
        Certifier_Reopened
        OverallStatus_Reopened
    }
    
    Certified --> [*] : Workflow Complete
    Reopened --> AreaOwnerAction : Area Owner must re-action
```

## Key Business Rules and Relationships

### 1. **User Role Management**
- **Many-to-Many Relationship**: Users can have multiple roles, roles can be assigned to multiple users
- **Junction Table**: `USER_ROLES` with additional `area_id` for area-specific assignments
- **Role Types**: Process Owner, Area Owner, Certifier

### 2. **Data Flow Hierarchy**
```
QUARTERS → DATA_UPLOADS → WORKFLOW_RECORDS
    ↓           ↓              ↓
USERS ←→ USERS ←→ USERS (Process Owner, Area Owner, Certifier)
```

### 3. **Workflow State Management**
- **Initial State**: All personas get pending statuses after file upload
- **Area Owner Action**: Updates trigger Process Owner status change to "pending_certification"
- **Certifier Decision**: 
  - **Certified**: Process Owner → "certified", workflow complete
  - **Reopened**: Both Process Owner and Area Owner → "reopened", requires re-action

### 4. **Audit Trail Relationships**
- **STATUS_HISTORY**: Tracks all status changes with persona context
- **COMMENTS**: Supports threading with self-referencing relationship
- **AUDIT_TRAIL**: System-wide audit logging for compliance
- **PREVIOUS_QUARTER_REFERENCES**: Links current records to historical data

### 5. **Access Control Patterns**
- **Area Owners**: Filter by `area_owner_id` and `area_code`
- **Certifiers**: Filter by `certifier_id` 
- **Process Owners**: Access all records for quarters they uploaded

### 6. **Historical Data Linking**
- **Self-Referencing**: `PREVIOUS_QUARTER_REFERENCES` links current and previous quarter records
- **Confidence Scoring**: Match quality assessment for automatic linking
- **JSON Criteria**: Flexible matching rules stored as JSONB

### 7. **Comment Threading**
- **Self-Referencing**: `parent_comment_id` enables reply chains
- **Persona Context**: Comments tagged by persona type for proper attribution
- **Soft Deletion**: `is_deleted` flag for audit trail preservation

This Mermaid ER diagram provides a comprehensive view of the workflow tool database with clear entity relationships, proper foreign key constraints, and complete audit trail capabilities suitable for ServiceNow-style workflow management.
