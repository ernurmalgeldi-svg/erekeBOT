from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
user_flows = {}

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Шифрование токенов
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key().decode())
fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

# Хранилище токенов пользователей (в памяти)
user_tokens = {}

CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
    }
}


def get_auth_url(user_id: int) -> str:
    """OAuth2 авторизация URL-ін қайтарады."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(user_id)
    )
    # Flow-ды сақтаймыз
    user_flows[user_id] = flow
    return auth_url

def exchange_code(user_id: int, code: str) -> bool:
    """Авторизация кодын токенге айырбастайды."""
    try:
        flow = user_flows.get(user_id)
        if not flow:
            return False
        
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes)
        }
        encrypted = fernet.encrypt(json.dumps(token_data).encode())
        user_tokens[user_id] = encrypted
        return True
    except Exception as e:
        logger.error(f"Токен алу қатесі: {e}")
        return False


def get_calendar_service(user_id: int):
    """Google Calendar сервисін қайтарады."""
    if user_id not in user_tokens:
        return None
    try:
        decrypted = fernet.decrypt(user_tokens[user_id])
        token_data = json.loads(decrypted)
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=token_data["scopes"]
        )
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        logger.error(f"Сервис қатесі: {e}")
        return None


async def create_event(user_id: int, title: str, date_str: str, time_str: str) -> str:
    """Google Calendar-ға оқиға қосады."""
    service = get_calendar_service(user_id)
    if not service:
        return "❌ Алдымен /gcal_auth арқылы Google аккаунтыңызды байланыстырыңыз!"

    try:
        dt_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_end = dt_start + timedelta(hours=1)

        event = {
            "summary": title,
            "start": {"dateTime": dt_start.isoformat(), "timeZone": "Asia/Almaty"},
            "end": {"dateTime": dt_end.isoformat(), "timeZone": "Asia/Almaty"},
        }
        result = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Оқиға жасалды: {result.get('htmlLink')}"
    except Exception as e:
        logger.error(f"Оқиға қосу қатесі: {e}")
        return f"❌ Қате: {str(e)}"


async def list_events(user_id: int) -> str:
    """Жақындағы оқиғаларды тізімдейді."""
    service = get_calendar_service(user_id)
    if not service:
        return "❌ Алдымен /gcal_auth арқылы байланыстырыңыз!"

    try:
        now = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        if not events:
            return "📅 Жақын арада оқиға жоқ."

        result = "📅 <b>Жақындағы оқиғалар:</b>\n\n"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            result += f"▪️ <b>{event['summary']}</b> — {start}\n"
        return result
    except Exception as e:
        return f"❌ Қате: {str(e)}"