import random
from locust import HttpUser, task, between

class TelegramWebhookLoadTester(HttpUser):
    # Имитация задержки мышления пользователя между отправкой сообщений
    wait_time = between(1.0, 3.0)

    @task(70)
    def send_text_query(self):
        """70% обычные текстовые вопросы"""
        payload = {
            "update_id": random.randint(100000, 999999),
            "message": {
                "message_id": random.randint(1, 10000),
                "from": {"id": random.randint(100, 999), "is_bot": False, "first_name": "LoadUser"},
                "chat": {"id": 55555, "type": "private"},
                "text": "Как настроить Docker Compose контекст для репликации PostgreSQL?"
            }
        }
        self.client.post("/webhook", json=payload, name="/webhook [Text]")

    @task(20)
    def send_voice_message(self):
        """20% голосовые сообщения (Voice Updates)"""
        payload = {
            "update_id": random.randint(100000, 999999),
            "message": {
                "message_id": random.randint(1, 10000),
                "from": {"id": random.randint(100, 999), "is_bot": False, "first_name": "LoadUser"},
                "chat": {"id": 55555, "type": "private"},
                "voice": {
                    "file_id": "AwACAgIAAxkBAAEExxx_mock_voice_file_id",
                    "duration": 5,
                    "file_size": 152400
                }
            }
        }
        self.client.post("/webhook", json=payload, name="/webhook [Voice]")

    @task(10)
    def send_photo_message(self):
        """10% изображения для анализа Vision-моделью"""
        payload = {
            "update_id": random.randint(100000, 999999),
            "message": {
                "message_id": random.randint(1, 10000),
                "from": {"id": random.randint(100, 999), "is_bot": False, "first_name": "LoadUser"},
                "chat": {"id": 55555, "type": "private"},
                "photo": [
                    {"file_id": "AgACAgIAAxkBA_mock_p1", "file_size": 2048, "width": 90, "height": 90},
                    {"file_id": "AgACAgIAAxkBA_mock_p2", "file_size": 45600, "width": 1280, "height": 720}
                ],
                "caption": "Суретте не бар? Түсіндір."
            }
        }
        self.client.post("/webhook", json=payload, name="/webhook [Photo]")