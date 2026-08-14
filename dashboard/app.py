import httpx
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RagDocs Enterprise — Ingestão", page_icon="📄")
st.title("📄 Ingestão de Documentos")
st.caption("Envie PDFs, Markdown, texto ou código-fonte para o índice do RAG.")

uploaded_files = st.file_uploader(
    "Arraste arquivos aqui ou clique para selecionar",
    accept_multiple_files=True,
    type=["pdf", "md", "txt", "py", "js", "ts", "java", "go"],
)

if uploaded_files:
    st.write(f"**{len(uploaded_files)} arquivo(s) selecionado(s)**")

if st.button("Enviar para ingestão", disabled=not uploaded_files):
    files_payload = [
        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
        for f in uploaded_files
    ]

    with st.spinner("Enviando e processando..."):
        try:
            response = httpx.post(
                f"{API_BASE_URL}/ingest/upload",
                files=files_payload,
                timeout=120.0,  # ingestão de PDFs grandes pode demorar
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            st.error(f"Falha ao conectar com a API: {exc}")
            st.stop()

    st.success(f"{data['completed']} de {data['total']} arquivo(s) processado(s) com sucesso.")
    if data["failed"] > 0:
        st.warning(f"{data['failed']} arquivo(s) falharam.")

    st.subheader("Detalhes")
    for result in data["results"]:
        icon = {"completed": "✅", "failed": "❌", "skipped_duplicate": "⏭️"}.get(
            result["status"], "❓"
        )
        st.write(f"{icon} **{result['file_name']}** — status: `{result['status']}`")
        if result.get("error_message"):
            st.caption(f"↳ erro: {result['error_message']}")