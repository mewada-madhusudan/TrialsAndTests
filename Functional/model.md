Sure! Here's a README based on the exact content you provided:

```markdown
# LauncherDB - Local Cache and One-Way Sync for Shared Database Access 🚀

## Overview 🌍

`LauncherDB` is a Python-based database handler designed to manage access to a shared SQLite database stored on a network drive. It offers advanced features for users who have direct access to the shared drive and those who don't, by providing a **local cache** of the database. It automatically synchronizes with the shared database to ensure data consistency while optimizing for **performance** and **reliability**.

### Key Features 🛠️

- **Automatic Mode Selection**: 
  - Automatically detects if the user has direct access to the shared drive. 
  - Users without access use a **local cache** that syncs from the shared drive.
  
- **One-Way Sync**: 
  - For users without access, the local copy is only synchronized **from** the shared drive (read-only for local copy).
  - The local cache is updated automatically when changes occur on the shared drive.
  
- **Bidirectional Sync for Write Operations**:
  - For users who have direct access, changes are written directly to the shared database.
  
- **Functional Account Support**:
  - Users without direct access can authenticate using a **functional account** to access the shared drive and sync the local copy.

- **Automatic Sync Check**:
  - A **refresh thread** periodically checks for updates in the shared database and forces a sync if new changes are detected.

- **Improved Error Handling**:
  - Gracefully handles network issues or missing access by falling back to local cache when needed.
  - Tracks sync status and logs changes made.

- **Configurable Cache Management**:
  - For users with direct access, the shared database file is accessed directly, while those without access use a local copy.

---

## Installation 🛠️

### Prerequisites

- Python 3.x
- `sqlite3` for database interaction (standard library)
- `PyQt6` (if you're using the UI integration)
  
### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo/launcher-db.git
    cd launcher-db
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage ⚡

### 1. **Basic Usage with Auto-Detection**

`LauncherDB` automatically detects if the user has direct access to the shared database and will fallback to local caching when necessary.

```python
from launcher_db import LauncherDB

# Initialize the database handler (it auto-detects access mode)
db = LauncherDB(db_path="\\\\server\\share\\launcher.db")

# Example: Get applications for a specific user
apps = db.get_user_applications("S-1-5-21-123456789-0987654321-123456789-1234")
```

### 2. **Usage with Functional Account Credentials**

When direct access is unavailable, you can provide functional account credentials to access the shared drive and sync the database.

```python
db = LauncherDB(
    db_path="\\\\server\\share\\launcher.db",
    functional_username="domain\\functional_user",
    functional_password="secure_password"
)

# Example: Get applications for a specific user
apps = db.get_user_applications("S-1-5-21-123456789-0987654321-123456789-1234")
```

### 3. **Forcing Local Cache (For Testing or Debugging)**

You can force the use of the local cache even if direct access is available.

```python
db = LauncherDB(
    db_path="\\\\server\\share\\launcher.db",
    force_local_cache=True
)

# Check if local cache is being used
if db.is_using_local_cache():
    print("Using local cache")
    sync_status = db.check_synced()
    if sync_status:
        is_synced, local_time, source_time = sync_status
        print(f"Sync status: {is_synced}, Local: {local_time}, Source: {source_time}")
else:
    print("Using direct access to shared database")
```

### 4. **Sync Status Check**

Check the sync status between the local cache and the shared drive.

```python
# Check if local cache is in sync with the shared database
is_synced, local_time, source_time = db.check_synced()
print(f"Database synced: {is_synced}, Local: {local_time}, Source: {source_time}")
```

### 5. **Force a Sync Manually**

You can manually trigger a sync from the shared drive to the local copy.

```python
db.force_sync()
```

---

## Internal Workflow 🧠

1. **Database Initialization**:
   - The `LauncherDB` class checks if the user has **direct access** to the shared database.
   - If access is available, the shared file is used directly.
   - If access isn't available, a **local cache** is created and periodically synchronized with the shared drive.

2. **Refresh Thread**:
   - A background thread (`RefreshThread`) periodically checks if the shared database has been updated by other users.
   - If new changes are found, it forces a sync to update the local cache.

3. **Sync Behavior**:
   - Users with direct access work directly with the shared drive.
   - Users without access operate on the **local cached copy** that syncs from the shared drive.

---

## Key Classes and Methods 📦

### `LauncherDB`

- **`__init__(self, db_path, functional_username=None, functional_password=None, force_local_cache=False)`**: Initializes the database handler.
- **`get_user_applications(self, user_sid)`**: Retrieves applications available to a user.
- **`check_synced(self)`**: Checks if the local cache is in sync with the shared drive.
- **`force_sync(self)`**: Forces a sync from the shared drive to the local cache.
- **`is_using_local_cache(self)`**: Checks if the local cache is being used.
  
### `UpdateCheckThread`

- Periodically checks for updates in the shared database and triggers a sync if necessary.

---

## UI Integration (Optional) 🎨

If you are using PyQt6, the database integration can be easily connected to your UI components. For example:

```python
from PyQt6.QtWidgets import QApplication
import sys
from main_window import MainWindow
from launcher_db import LauncherDB

# Initialize database and pass it to the UI
db = LauncherDB(db_path="\\\\server\\share\\launcher.db")

# Create the application window
app = QApplication(sys.argv)
window = MainWindow(db=db)
window.show()
sys.exit(app.exec())
```

---

## Future Enhancements 🚧

- **Conflict Resolution**: Implement conflict resolution mechanisms when changes are detected both locally and on the shared drive.
- **More Robust Sync Algorithms**: Improve the sync algorithms for more efficient handling of large datasets and low-bandwidth scenarios.
- **Better Error Handling**: Provide more detailed diagnostics for sync failures and other operational issues.

---

## Contributing 💡

Feel free to fork this repository and submit pull requests. If you encounter any bugs or have feature requests, please open an issue on GitHub.

---

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

This is the exact content you provided with minimal changes, formatted into a complete README. It includes everything from the system features, code usage, internal workflow, to UI integration examples.
