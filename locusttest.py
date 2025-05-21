from locust import HttpUser, task, between
class StreamlitUser(HttpUser):
    # target host where Streamlit is running:
    host = "http://localhost:8501"
    wait_time = between(1, 3)

    @task(2)
    def view_home(self):
        # load the main dashboard page
        self.client.get("/")

    @task(1)
    def fetch_static_assets(self):
        # Streamlit serves some JS and CSS under /static/...
        # you can add more asset paths as you see in your browser’s network tab
        self.client.get("/static/js/main.js")
        self.client.get("/static/css/main.css")
