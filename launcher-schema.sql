-- Admins table for administrative users
CREATE TABLE admins (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    sid TEXT NOT NULL UNIQUE,
    email TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost Centers table
CREATE TABLE cost_centers (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Line of Business (LOB) table
CREATE TABLE lobs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status table for application statuses
CREATE TABLE statuses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application Fields table (for dynamic fields)
CREATE TABLE fields (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    field_type TEXT NOT NULL, -- e.g., 'text', 'number', 'date', etc.
    is_required BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    exe_path TEXT NOT NULL,
    lob_id INTEGER,
    status_id INTEGER,
    cost_center_id INTEGER,
    version TEXT,
    owner_sid TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lob_id) REFERENCES lobs(id),
    FOREIGN KEY (status_id) REFERENCES statuses(id),
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
);

-- Application Field Values table (for dynamic field values)
CREATE TABLE application_field_values (
    application_id INTEGER,
    field_id INTEGER,
    field_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (application_id, field_id),
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (field_id) REFERENCES fields(id)
);

-- Regular Users table
CREATE TABLE regular_users (
    sid TEXT PRIMARY KEY,
    display_name TEXT,
    email TEXT,
    cost_center_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
);

-- STO Superadmins table (separated from regular users)
CREATE TABLE sto_superadmins (
    id INTEGER PRIMARY KEY,
    sid TEXT NOT NULL UNIQUE,
    display_name TEXT,
    email TEXT,
    cost_center_id INTEGER,
    role TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
);

-- User Application Access table (for regular users)
CREATE TABLE user_application_access (
    user_sid TEXT,
    application_id INTEGER,
    granted_by TEXT,
    granted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    PRIMARY KEY (user_sid, application_id),
    FOREIGN KEY (user_sid) REFERENCES regular_users(sid),
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (granted_by) REFERENCES sto_superadmins(sid)
);

-- Create indexes for better performance
CREATE INDEX idx_applications_lob ON applications(lob_id);
CREATE INDEX idx_applications_status ON applications(status_id);
CREATE INDEX idx_applications_costcenter ON applications(cost_center_id);
CREATE INDEX idx_users_costcenter ON regular_users(cost_center_id);
CREATE INDEX idx_sto_costcenter ON sto_superadmins(cost_center_id);
CREATE INDEX idx_user_access_app ON user_application_access(application_id);
CREATE INDEX idx_app_field_values_field ON application_field_values(field_id);
