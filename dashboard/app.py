import time

import httpx
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"
POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 180

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

    with st.spinner("Enviando arquivos..."):
        try:
            response = httpx.post(
                f"{API_BASE_URL}/ingest/upload",
                files=files_payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            st.error(f"Falha ao conectar com a API: {exc}")
            st.stop()

    # Documentos que entraram na fila de background e ainda precisam ser acompanhados
    tracked = {
        r["document_id"]: r
        for r in data["results"]
        if r["document_id"] and r["status"] == "processing"
    }
    # Resultados que já vieram resolvidos (duplicados, ou falha antes da fila)
    final_results = [r for r in data["results"] if r["document_id"] not in tracked]

    status_placeholder = st.empty()

    if tracked:
        with st.spinner(f"Processando {len(tracked)} documento(s)..."):
            elapsed = 0
            while elapsed < POLL_TIMEOUT_SECONDS:
                still_processing = []
                for doc_id, result in list(tracked.items()):
                    resp = httpx.get(f"{API_BASE_URL}/documents/{doc_id}")
                    if resp.status_code != 200:
                        continue
                    doc = resp.json()
                    result["status"] = doc["status"]
                    result["error_message"] = doc.get("error_message")

                    if doc["status"] in ("completed", "failed"):
                        final_results.append(result)
                        del tracked[doc_id]
                    else:
                        still_processing.append(result["file_name"])

                status_placeholder.write(
                    f"Aguardando: {', '.join(still_processing)}" if still_processing else ""
                )

                if not tracked:
                    break

                time.sleep(POLL_INTERVAL_SECONDS)
                elapsed += POLL_INTERVAL_SECONDS

            # Timeout: o que sobrou em `tracked` ainda está processando de verdade
            final_results.extend(tracked.values())

    status_placeholder.empty()

    completed_count = sum(1 for r in final_results if r["status"] == "completed")
    failed_count = sum(1 for r in final_results if r["status"] == "failed")
    still_processing_count = sum(1 for r in final_results if r["status"] == "processing")

    st.success(f"{completed_count} de {len(final_results)} arquivo(s) processado(s) com sucesso.")
    if failed_count > 0:
        st.warning(f"{failed_count} arquivo(s) falharam.")
    if still_processing_count > 0:
        st.info(
            f"{still_processing_count} arquivo(s) ainda em processamento "
            f"(demorando mais que o esperado). Atualize a página em instantes."
        )

    st.subheader("Detalhes")
    for result in final_results:
        icon = {
            "completed": "✅",
            "failed": "❌",
            "skipped_duplicate": "⏭️",
            "processing": "⏳",
        }.get(result["status"], "❓")
        st.write(f"{icon} **{result['file_name']}** — status: `{result['status']}`")
        if result.get("error_message"):
            st.caption(f"↳ erro: {result['error_message']}")