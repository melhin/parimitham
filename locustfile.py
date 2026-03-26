from locust import HttpUser, between, task


class HelloWorldUser(HttpUser):
    host = "http://127.0.0.1:8008"
    wait_time = between(1, 3)

    @task(3)
    def hit_dhello_endpoint(self):
        self.client.get("/dhello/")

    @task(1)
    def hit_another_endpoint(self):
        self.client.get("/hello/")
