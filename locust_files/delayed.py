from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:9001"

    @task
    def dhello(self):
        self.client.get("/dhello")
