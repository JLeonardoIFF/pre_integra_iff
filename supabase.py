from supabase import create_client

# --- configuração ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEBOUNCE_SECONDS = 2  # salva no máximo a cada 2s para evitar spam

# helpers DB
def get_progress_for_user(user_id):
    resp = supabase.table("user_progress").select("progress").eq("user_id", user_id).single().execute()
    # resp.data pode ser None se não existir
    data = getattr(resp, "data", None)
    if data:
        return data.get("progress", 0)
    return 0

def save_progress_for_user(user_id, progress):
    # upsert: insere ou atualiza
    resp = supabase.table("user_progress").upsert({
        "user_id": user_id,
        "progress": int(progress),
        "updated_at": "now()"r
    }).execute()
    return resp