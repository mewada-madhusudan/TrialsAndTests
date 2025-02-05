from PyQt6.QtWidgets import (QProgressDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
import asyncio
import aiohttp

async def verify_user_id(session, user_id):
    """
    Verify a single user ID using the API
    Replace the URL and any necessary headers/auth for your API
    """
    try:
        async with session.get(f'YOUR_API_URL/verify/{user_id}') as response:
            return user_id, response.status == 200
    except:
        return user_id, False

async def verify_multiple_ids(user_ids):
    """
    Verify multiple user IDs concurrently
    """
    async with aiohttp.ClientSession() as session:
        tasks = [verify_user_id(session, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return {uid: is_valid for uid, is_valid in results}

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
    progress = QProgressDialog("Verifying user IDs...", None, 0, 0, self)
    progress.setWindowTitle("Please Wait")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.show()

    def handle_verification_complete(future):
        progress.close()
        verification_results = future.result()
        
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

    # Run verification in a separate thread to avoid blocking the UI
    loop = asyncio.new_event_loop()
    future = asyncio.run_coroutine_threadsafe(
        verify_multiple_ids(new_users_list),
        loop
    )
    future.add_done_callback(handle_verification_complete)
