import os
import csv
import io
import psycopg2
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR
from dotenv import load_dotenv

# .env файлын жүктеу
load_dotenv()

# Рөлдік жүйесі бар жаңа MCP сервер
mcp = FastMCP("Postgres-Secure-Server")

def get_db_connection():
    """PostgreSQL базасына қосылу"""
    return psycopg2.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )

def check_role_permission(ctx: Context, required_roles: list):
    """
    Сессияны бастау кезінде (initialization) берілген рөлді тексеру функциясы.
    Талапқа сай, рұқсат болмаса -32603 (INTERNAL_ERROR) қатесін қайтарады.
    """
    # Клиент сессия ашқанда жіберген initialization_options ішінен рөлді іздейміз
    init_options = getattr(ctx, "initialization_options", {}) or {}
    user_role = init_options.get("role", "student") # Егер рөл берілмесе, дефолт бойынша - student
    
    if user_role not in required_roles:
        # Тапсырманың басты критерийі: қате коды -32603 болуы шарт
        raise McpError(
            code=-32603,  # Internal error коды
            message=f"Рұқсат берілмеген! Сіздің рөліңіз: '{user_role}'. Бұл құралды қолдану үшін мына рөлдер керек: {required_roles}"
        )
    return user_role


# --- 1-ҚҰРАЛ: Қолданушыларды анықтау (Тек admin мен teacher-ге рұқсат) ---
@mcp.tool()
async def query_users(ctx: Context) -> str:
    """Базадағы барлық қолданушылардың ID тізімін қайтарады. (Рөл: admin, teacher)"""
    check_role_permission(ctx, ["admin", "teacher"])
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT user_id FROM messages;")
            rows = cur.fetchall()
        conn.close()
        
        if not rows:
            return "Базада әлі ешқандай қолданушы тіркелмеген."
            
        user_ids = [str(row[0]) for row in rows]
        return f"Базадағы қолданушылар ID тізімі: {', '.join(user_ids)}"
    except McpError as mcp_err:
        raise mcp_err
    except Exception as e:
        raise McpError(code=-32603, message=f"База қатесі: {e}")


# --- 2-ҚҰРАЛ: Қолданушы статистикасы (Барлық рөлдерге, студентке де рұқсат) ---
@mcp.tool()
async def get_user_stats(user_id: int, ctx: Context) -> str:
    """Нақты қолданушының хабарламалар санын есептейді. (Рөл: student, teacher, admin)"""
    # Барлық рөлдерге рұқсат
    check_role_permission(ctx, ["student", "teacher", "admin"])
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM messages WHERE user_id = %s;", (user_id,))
            count = cur.fetchone()[0]
        conn.close()
        return f"Қолданушы {user_id} базаға жалпы {count} хабарлама жіберген."
    except McpError as mcp_err:
        raise mcp_err
    except Exception as e:
        raise McpError(code=-32603, message=f"База қатесі: {e}")


# --- 3-ҚҰРАЛ: CSV форматқа экспорттау (ТЕК ҚАНА admin-ге рұқсат) ---
@mcp.tool()
async def export_to_csv(ctx: Context) -> str:
    """Базадағы барлық чат тарихын таза CSV форматында экспорттайды. (Рөл: ТЕК admin)"""
    # Студент немесе мұғалім шақырса, бірден -32603 қатесі ұшады
    check_role_permission(ctx, ["admin"])
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_id, user_message, bot_response, created_at FROM messages;")
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
        conn.close()

        if not rows:
            return "Экспорттайтын ештеңе жоқ, база бос."

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(colnames)
        writer.writerows(rows)
        
        return output.getvalue()
    except McpError as mcp_err:
        raise mcp_err
    except Exception as e:
        raise McpError(code=-32603, message=f"База қатесі: {e}")

if __name__ == "__main__":
    # Сервер stdio транспорты арқылы іске қосылады
    mcp.run(transport="stdio")