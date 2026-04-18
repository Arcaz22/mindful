import hashlib
import uuid

import httpx
import streamlit as st


st.set_page_config(
    page_title="Mindful Chat",
    page_icon=":speech_balloon:",
    layout="wide",
)


def build_client_identity() -> tuple[str, str, str]:
    headers = st.context.headers
    forwarded_for = headers.get("X-Forwarded-For", "")
    forwarded_ip = forwarded_for.split(",")[0].strip() if forwarded_for else ""
    ip_address = st.context.ip_address or forwarded_ip or headers.get("X-Real-Ip", "")
    user_agent = headers.get("User-Agent", "")
    accept_language = headers.get("Accept-Language", "")

    raw_identity = "|".join(
        part for part in (ip_address, user_agent, accept_language) if part
    )
    if not raw_identity:
        raw_identity = st.session_state.get("anonymous_identity_seed", str(uuid.uuid4()))
        st.session_state.anonymous_identity_seed = raw_identity

    identity_hash = hashlib.sha256(raw_identity.encode("utf-8")).hexdigest()
    user_id = f"user-{identity_hash[:12]}"
    visitor_id = f"visitor-{identity_hash[:16]}"
    identity_source = ip_address or "anonymous-session"
    return user_id, visitor_id, identity_source


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Halo, saya siap membantu berdasarkan knowledge base yang tersedia. "
                    "Ketik pertanyaan Anda untuk memulai."
                ),
            }
        ]
    user_id, visitor_id, identity_source = build_client_identity()
    st.session_state.user_id = user_id
    st.session_state.visitor_id = visitor_id
    st.session_state.identity_source = identity_source
    if "last_meta" not in st.session_state:
        st.session_state.last_meta = None


def render_sidebar() -> str:
    with st.sidebar:
        st.title("Mindful UI")
        st.caption("Frontend Streamlit untuk backend chat yang sudah ada.")

        api_base_url = st.text_input(
            "Backend URL",
            value="http://localhost:8000",
            help="Alamat backend FastAPI yang menjalankan endpoint /chat.",
        ).rstrip("/")

        st.markdown("**Identitas Pengguna**")
        st.caption("Dibuat otomatis dari IP/header request dan hanya ditampilkan sebagai info.")
        st.text(f"User ID: {st.session_state.user_id}")
        st.text(f"Visitor ID: {st.session_state.visitor_id}")
        st.caption(f"Sumber identitas: {st.session_state.identity_source}")

        if st.button("Reset Chat", use_container_width=True):
            preserved_user = st.session_state.user_id
            preserved_visitor = st.session_state.visitor_id
            preserved_source = st.session_state.identity_source
            preserved_seed = st.session_state.get("anonymous_identity_seed")
            st.session_state.clear()
            init_state()
            st.session_state.user_id = preserved_user
            st.session_state.visitor_id = preserved_visitor
            st.session_state.identity_source = preserved_source
            if preserved_seed:
                st.session_state.anonymous_identity_seed = preserved_seed
            st.rerun()

        st.divider()
        st.markdown(
            """
            **Cara pakai**

            1. Jalankan backend FastAPI.
            2. Jalankan Streamlit app ini.
            3. Kirim pertanyaan lewat kolom chat.
            """
        )

        if st.session_state.last_meta:
            st.divider()
            st.markdown("**Info respons terakhir**")
            st.write(f"Model: `{st.session_state.last_meta['model_used']}`")
            st.write(f"Sisa chat: `{st.session_state.last_meta['remaining_chats']}`")
            st.write(f"Context IDs: `{st.session_state.last_meta['context_ids']}`")

    return api_base_url


def render_messages() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("meta"):
                st.caption(message["meta"])


def ask_backend(api_base_url: str, prompt: str) -> dict:
    payload = {
        "user_id": st.session_state.user_id,
        "message": prompt,
        "visitor_id": st.session_state.visitor_id,
    }
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{api_base_url}/chat", json=payload)
        response.raise_for_status()
        return response.json()


def main() -> None:
    init_state()
    api_base_url = render_sidebar()

    st.title("Mindful Chat")
    st.caption("Streamlit interface untuk menguji knowledge base chat yang tersedia saat ini.")

    render_messages()

    prompt = st.chat_input("Tulis pertanyaan Anda...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Memproses jawaban..."):
            try:
                result = ask_backend(api_base_url, prompt)
                meta = (
                    f"Model: {result['model_used']} | "
                    f"Sisa chat: {result['remaining_chats']} | "
                    f"Context IDs: {result.get('context_ids') or []}"
                )
                st.markdown(result["answer"])
                st.caption(meta)
                st.session_state.last_meta = result
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "meta": meta,
                    }
                )
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text
                message = f"Backend mengembalikan error {exc.response.status_code}: {detail}"
                st.error(message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message}
                )
            except httpx.HTTPError as exc:
                message = (
                    "Tidak bisa terhubung ke backend. "
                    f"Periksa URL backend dan pastikan server aktif. Detail: {exc}"
                )
                st.error(message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message}
                )


if __name__ == "__main__":
    main()
