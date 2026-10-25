import base64
import requests
import streamlit as st
from openai import OpenAI

# ==========================================
# MY AI - CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="My AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"
IMAGE_MODEL = "gpt-image-2.5-flare"

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_secret(name, default=""):
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def search_web(query):
    api_key = get_secret("TAVILY_API_KEY")

    if not api_key:
        return "Pencarian web belum dikonfigurasi."

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True
            },
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        results = []

        if data.get("answer"):
            results.append("Ringkasan pencarian:\n" + data["answer"])

        for item in data.get("results", []):
            results.append(
                "Judul: " + item.get("title", "") +
                "\nInformasi: " + item.get("content", "")
            )

        return "\n\n".join(results) or "Tidak ada hasil ditemukan."

    except Exception:
        return "Pencarian web gagal. Periksa koneksi dan API key."


def ask_ollama(messages, extra_instruction=""):
    system_prompt = (
        "Kamu adalah My AI, asisten AI yang ramah, "
        "akurat, dan menjawab dalam bahasa pengguna. "
        "Jangan mengaku dibuat oleh perusahaan lain. "
        "Jangan mengarang fakta jika tidak tahu. "
        + extra_instruction
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages
        ]
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180
    )
    response.raise_for_status()

    return response.json()["message"]["content"]


def make_image(prompt, size):
    api_key = get_secret("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY belum dipasang di secrets.toml."
        )

    client = OpenAI(
        api_key=api_key,
        timeout=180,
        max_retries=1
    )

    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=size,
        quality="medium",
        n=1
    )

    image_data = result.data[0].b64_json

    if not image_data:
        raise ValueError("API tidak mengembalikan data gambar.")

    return base64.b64decode(image_data)


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "logged_in": False,
    "role": "",
    "username": "",
    "chats": {},
    "active_chat": None,
    "learned_instruction": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# LOGIN
# ==========================================

if not st.session_state.logged_in:
    st.markdown(
        "<h1 style='text-align:center'>🤖 My AI</h1>"
        "<p style='text-align:center'>Your Personal AI Assistant</p>",
        unsafe_allow_html=True
    )

    _, center, _ = st.columns([1, 1.2, 1])

    with center:
        st.subheader("Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password"
            )
            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submitted:
            dev_user = get_secret("DEVELOPER_USERNAME")
            dev_pass = get_secret("DEVELOPER_PASSWORD")
            user_name = get_secret("USER_USERNAME")
            user_pass = get_secret("USER_PASSWORD")

            if (
                dev_user and dev_pass
                and username == dev_user
                and password == dev_pass
            ):
                st.session_state.logged_in = True
                st.session_state.role = "developer"
                st.session_state.username = username
                st.rerun()

            elif (
                user_name and user_pass
                and username == user_name
                and password == user_pass
            ):
                st.session_state.logged_in = True
                st.session_state.role = "user"
                st.session_state.username = username
                st.rerun()

            else:
                st.error("Username atau password salah.")

    st.stop()


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown("## 🤖 My AI")
    st.caption("Your Personal AI Assistant")

    st.write("Login sebagai:", st.session_state.username)
    st.caption("Role: " + st.session_state.role.title())

    if st.button("＋ Chat Baru", use_container_width=True):
        chat_id = str(len(st.session_state.chats) + 1)
        st.session_state.chats[chat_id] = {
            "title": "Chat Baru",
            "messages": []
        }
        st.session_state.active_chat = chat_id
        st.rerun()

    st.divider()
    st.markdown("### Riwayat Chat")

    for chat_id, chat in reversed(
        list(st.session_state.chats.items())
    ):
        if st.button(
            "💬 " + chat["title"][:35],
            key="open_" + chat_id,
            use_container_width=True
        ):
            st.session_state.active_chat = chat_id
            st.rerun()

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = ""
        st.session_state.username = ""
        st.rerun()


# Buat chat otomatis jika belum ada.
if not st.session_state.active_chat:
    chat_id = str(len(st.session_state.chats) + 1)
    st.session_state.chats[chat_id] = {
        "title": "Chat Baru",
        "messages": []
    }
    st.session_state.active_chat = chat_id

current_chat = st.session_state.chats[
    st.session_state.active_chat
]


# ==========================================
# MAIN HEADER
# ==========================================

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px">
        <div style="
            font-size:38px;
            background:linear-gradient(135deg,#6C63FF,#00D4FF);
            border-radius:14px;
            padding:8px 12px;
        ">🤖</div>
        <div>
            <h1 style="margin:0">My AI</h1>
            <p style="margin:0;color:gray">
                Your Personal AI Assistant
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# MAIN FEATURES
# ==========================================

tab_names = ["💬 Chat", "🎨 Buat Gambar"]

if st.session_state.role == "developer":
    tab_names.append("🛠️ Ajar AI")

tabs = st.tabs(tab_names)


# ==========================================
# CHAT TAB
# ==========================================

with tabs[0]:
    st.caption("AI lokal dengan Ollama")

    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input(
        "Tanyakan sesuatu kepada My AI..."
    )

    if user_input:
        if current_chat["title"] == "Chat Baru":
            current_chat["title"] = user_input[:35]

        current_chat["messages"].append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("My AI sedang berpikir..."):
                try:
                    instruction = st.session_state.learned_instruction

                    # Pencarian web bisa diminta secara eksplisit.
                    lowered = user_input.lower()
                    search_terms = [
                        "cari di internet",
                        "cari di web",
                        "berita terbaru",
                        "informasi terbaru",
                        "hari ini",
                        "harga terbaru",
                        "siapa presiden sekarang",
                        "tanggal berapa sekarang"
                    ]

                    web_context = ""

                    if any(term in lowered for term in search_terms):
                        web_context = search_web(user_input)

                    messages = current_chat["messages"][:-1]

                    if web_context:
                        messages.append({
                            "role": "user",
                            "content": (
                                "Gunakan hasil pencarian web berikut "
                                "untuk menjawab pertanyaan pengguna. "
                                "Jika informasi tidak cukup, katakan "
                                "secara jujur.\n\n"
                                + web_context
                                + "\n\nPertanyaan: "
                                + user_input
                            )
                        })
                    else:
                        messages.append({
                            "role": "user",
                            "content": user_input
                        })

                    answer = ask_ollama(
                        messages,
                        instruction
                    )

                    st.markdown(answer)

                    current_chat["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Ollama tidak terhubung. "
                        "Pastikan Ollama sedang berjalan."
                    )

                except Exception as error:
                    st.error("Gagal mendapatkan jawaban dari AI.")
                    st.caption(str(error))


# ==========================================
# IMAGE GENERATOR TAB
# ==========================================

with tabs[1]:
    st.subheader("🎨 AI Image Generator")
    st.write(
        "Ubah ide dan deskripsi teks menjadi gambar."
    )

    with st.form("image_form"):
        image_prompt = st.text_area(
            "Deskripsikan gambar yang kamu inginkan",
            placeholder=(
                "Contoh: robot AI futuristik hitam dan ungu, "
                "mata bercahaya, kota cyberpunk, sinematik..."
            ),
            height=130
        )

        image_size = st.selectbox(
            "Ukuran gambar",
            ["1024x1024", "1536x1024", "1024x1536"],
            format_func=lambda size: {
                "1024x1024": "Persegi",
                "1536x1024": "Landscape",
                "1024x1536": "Portrait"
            }[size]
        )

        generate = st.form_submit_button(
            "✨ Buat Gambar",
            type="primary",
            use_container_width=True
        )

    if generate:
        if not image_prompt.strip():
            st.warning("Tulis deskripsi gambar terlebih dahulu.")
        else:
            try:
                with st.spinner(
                    "AI sedang membuat gambar. Tunggu sebentar..."
                ):
                    image_bytes = make_image(
                        image_prompt.strip(),
                        image_size
                    )

                st.success("Gambar berhasil dibuat!")
                st.image(
                    image_bytes,
                    caption="Dibuat oleh My AI",
                    use_container_width=True
                )

                st.download_button(
                    "⬇️ Download Gambar",
                    data=image_bytes,
                    file_name="my_ai_image.png",
                    mime="image/png",
                    use_container_width=True
                )

            except Exception as error:
                st.error(
                    "Gambar gagal dibuat. Periksa API key, "
                    "akses model, billing, dan koneksi internet."
                )
                st.caption(str(error))


# ==========================================
# DEVELOPER-ONLY LEARNING TAB
# ==========================================

if st.session_state.role == "developer":
    with tabs[2]:
        st.subheader("🛠️ Ajar My AI")
        st.info(
            "Fitur ini hanya ditampilkan untuk akun Developer."
        )

        new_instruction = st.text_area(
            "Instruksi tambahan untuk AI",
            value=st.session_state.learned_instruction,
            height=180,
            placeholder=(
                "Contoh: Jawab dengan bahasa Indonesia "
                "yang santai dan berikan contoh praktis."
            )
        )

        if st.button(
            "💾 Simpan Instruksi",
            type="primary"
        ):
            st.session_state.learned_instruction = new_instruction
            st.success("Instruksi disimpan untuk sesi ini.")