import yaml
from streamlit_authenticator import Hasher
from supabase import create_client

# ------------------------
# CONFIG SUPABASE
# ------------------------
SUPABASE_URL = st.secrets["SUPABASE"]["URL"]
SUPABASE_KEY = st.secrets["SUPABASE"]["KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# LIRE USERS YAML
# ------------------------
with open("users.yaml") as f:
    users_config = yaml.safe_load(f)

credentials = users_config["usernames"]

# ------------------------
# HASH DES MOTS DE PASSE
# ------------------------
hasher = Hasher()
credentials = hasher.hash_passwords(credentials)

# ------------------------
# INSÉRER DANS SUPABASE
# ------------------------
for username, info in credentials.items():
    # Vérifier si l'utilisateur existe déjà
    exists = supabase.table("users").select("username").eq("username", username).execute().data
    if not exists:
        supabase.table("users").insert({
            "username": username,
            "name": info["name"],
            "role": info.get("role", "user"),
            "password_hash": info["password"],  # hash
            "active": True
        }).execute()
        print(f"✅ Utilisateur ajouté : {username}")
    else:
        print(f"⚠️ Utilisateur déjà existant : {username}")
