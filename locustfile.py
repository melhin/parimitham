import io
import random
import string

from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:8001"

    # @task
    # def index_page(self):
    #    self.client.get("/")

    @task
    def upload_file(self):
        # Create a dummy file in memory
        file_size = random.randint(1024, 10240)  # 1KB to 10KB
        file_content = "".join(random.choices(string.ascii_letters + string.digits, k=file_size))
        file_name = f"test_file_{random.randint(1, 1000)}.txt"

        # Create a file-like object
        file_obj = io.BytesIO(file_content.encode("utf-8"))

        # Prepare the files dictionary for the request
        files = {"file": (file_name, file_obj, "text/plain")}

        # Send the POST request
        with self.client.post(
            "/upload/",  # Update this with your actual endpoint URL
            files=files,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Failed to upload file. Status code: {response.status_code}, Response: {response.text}"
                )
            else:
                try:
                    response_data = response.json()
                    if response_data.get("status") != "success":
                        response.failure(f"Upload failed. Response: {response.text}")
                except ValueError:
                    response.failure("Invalid JSON response")
