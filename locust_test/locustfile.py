import os
import random

from locust import HttpUser, between, task

test_files_dir = "locust_test/test_files"
files = os.listdir(test_files_dir)


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8001"

    # @task
    # def index_page(self):
    #    self.client.get("/")

    @task
    def upload_file(self):
        # Select a random file from the test_files directory
        selected_file = random.choice(files)
        file_path = os.path.join(test_files_dir, selected_file)

        # Open and read the selected file
        with open(file_path, "rb") as file:
            file_content = file.read()

        # Upload the file
        with self.client.post(
            "/upload",
            files={"file": (selected_file, file_content)},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to upload file: {response.text}")
            else:
                response.success()
