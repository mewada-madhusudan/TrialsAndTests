from PyQt6.QtWidgets import (QProgressDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
import asyncio
import aiohttp

class VerificationWorker(QObject):
    finished = pyqtSignal(dict)
    
    def __init__(self, user_ids):
        super().__init__()
        self.user_ids = user_ids

    async def verify_user_id(self, session, user_id):
        """
        Verify a single user ID using the API
        Replace the URL and any necessary headers/auth for your API
        """
        try:
            # Replace with your actual API endpoint
            async with session.get(f'YOUR_API_URL/verify/{user_id}') as response:
                return user_id, response.status == 200
        except:
            return user_id, False

    async def verify_multiple_ids(self):
        """
        Verify multiple user IDs concurrently
        """
        async with aiohttp.ClientSession() as session:
            tasks = [self.verify_user_id(session, uid) for uid in self.user_ids]
            results = await asyncio.gather(*tasks)
            return {uid: is_valid for uid, is_valid in results}

    def run(self):
        """
        Run the verification process
        """
        async def run_async():
            results = await self.verify_multiple_ids()
            self.finished.emit(results)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async())
        loop.close()

def add_multiple_users(self):
    if not self.app_list.currentItem():
        QMessageBox.warning(self, "No Application Selected",
                          "Please select an application first.",
                          QMessageBox.StandardButton.Ok)
        return

    new_users = self.new_users_text.toPlainText().strip()
    if not new_users:
        return

    # Split by newlines and commas, then clean up
    new_users_list = set()
    for line in new_users.split('\n'):
        new_users_list.update(uid.strip() for uid in line.split(',') if uid.strip())

    if not new_users_list:
        return

    # Create progress dialog
    self.progress = QProgressDialog("Verifying user IDs...", None, 0, 0, self)
    self.progress.setWindowTitle("Please Wait")
    self.progress.setWindowModality(Qt.WindowModality.WindowModal)
    self.progress.show()

    # Create worker thread
    self.thread = QThread()
    self.worker = VerificationWorker(new_users_list)
    self.worker.moveToThread(self.thread)

    # Connect signals
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.handle_verification_complete)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)

    # Start the thread
    self.thread.start()

def handle_verification_complete(self, verification_results):
    """
    Handle the completion of ID verification
    """
    self.progress.close()
    
    valid_ids = {uid for uid, is_valid in verification_results.items() if is_valid}
    invalid_ids = {uid for uid, is_valid in verification_results.items() if not is_valid}

    if invalid_ids:
        # Keep invalid IDs in the text edit
        self.new_users_text.setPlainText('\n'.join(invalid_ids))
        QMessageBox.warning(
            self,
            "Invalid IDs Found",
            f"The following IDs could not be verified and were not added:\n\n{', '.join(invalid_ids)}",
            QMessageBox.StandardButton.Ok
        )

    if valid_ids:
        # Add verified IDs to the DataFrame
        app_name = self.app_list.currentItem().data(Qt.ItemDataRole.UserRole)
        app_idx = self.df[self.df['application_name'] == app_name].index[0]
        current_sids = set(self.df.at[app_idx, 'sids'].split(','))
        updated_sids = current_sids.union(valid_ids)
        self.df.at[app_idx, 'sids'] = ','.join(updated_sids)
        self.show_application_users(self.app_list.currentItem())
        self.show_success_message(f"Successfully added {len(valid_ids)} verified user(s)")
