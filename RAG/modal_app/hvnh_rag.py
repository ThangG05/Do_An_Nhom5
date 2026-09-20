"""Authenticated BAAI/bge-m3 embedding service deployed on Modal."""
from typing import Literal

import modal
from fastapi import HTTPException
from pydantic import BaseModel, Field


APP_NAME = "hvnh_rag"
MODEL_ID = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
VECTOR_DIMENSIONS = 1024
MAX_BATCH_SIZE = 64
MAX_TEXT_CHARS = 8_192
MAX_REQUEST_CHARS = 100_000


def download_model() -> None:
    from sentence_transformers import SentenceTransformer

    SentenceTransformer(MODEL_ID, revision=MODEL_REVISION)


image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "fastapi==0.116.1",
        "torch==2.7.1",
        "transformers==4.57.6",
        "sentence-transformers==5.1.1",
        extra_options="--index-strategy unsafe-best-match",
        extra_index_url="https://download.pytorch.org/whl/cu128",
    )
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"})
    .run_function(download_model)
)

ocr_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("tesseract-ocr", "tesseract-ocr-vie")
    .uv_pip_install("fastapi==0.116.1", "pymupdf==1.26.4", "pytesseract==0.3.13", "Pillow==11.3.0")
)

app = modal.App(APP_NAME)

with image.imports():
    from sentence_transformers import SentenceTransformer


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=MAX_BATCH_SIZE)
    input_type: Literal["document", "query"] = "document"


class EmbedResponse(BaseModel):
    model: str
    dimensions: int
    count: int
    embeddings: list[list[float]]


@app.cls(
    image=image,
    gpu="T4",
    timeout=10 * 60,
    scaledown_window=5 * 60,
    min_containers=0,
    max_containers=3,
)
class BgeM3:
    @modal.enter()
    def load_model(self) -> None:
        self.model = SentenceTransformer(MODEL_ID, revision=MODEL_REVISION, device="cuda")

    @staticmethod
    def _validate(texts: list[str]) -> None:
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("texts must contain non-empty strings")
        if any(len(text) > MAX_TEXT_CHARS for text in texts):
            raise ValueError("one or more texts exceed the character limit")
        if sum(map(len, texts)) > MAX_REQUEST_CHARS:
            raise ValueError("request exceeds the total character limit")

    def _encode(self, texts: list[str]) -> list[list[float]]:
        self._validate(texts)
        vectors = self.model.encode(
            texts,
            batch_size=min(16, len(texts)),
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        if vectors.ndim != 2 or vectors.shape[1] != VECTOR_DIMENSIONS:
            raise RuntimeError("unexpected embedding dimensions")
        return vectors.tolist()

    @modal.method()
    def embed(self, texts: list[str], input_type: str = "document") -> dict:
        if input_type not in {"document", "query"}:
            raise ValueError("input_type must be document or query")
        vectors = self._encode(texts)
        return {
            "model": MODEL_ID,
            "dimensions": VECTOR_DIMENSIONS,
            "count": len(vectors),
            "embeddings": vectors,
        }

    @modal.fastapi_endpoint(
        method="POST",
        label="embed",
        docs=False,
        requires_proxy_auth=True,
    )
    def embed_http(self, request: EmbedRequest) -> EmbedResponse:
        try:
            vectors = self._encode(request.texts)
            return EmbedResponse(
                model=MODEL_ID,
                dimensions=VECTOR_DIMENSIONS,
                count=len(vectors),
                embeddings=vectors,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None


@app.cls(
    image=ocr_image,
    cpu=2.0,
    memory=4096,
    timeout=15 * 60,
    scaledown_window=2 * 60,
    min_containers=0,
    max_containers=2,
)
class PdfOCR:
    @modal.method()
    def extract(self, pdf_bytes: bytes, max_pages: int = 200) -> dict:
        from io import BytesIO

        import fitz
        from PIL import Image
        import pytesseract

        if not pdf_bytes or len(pdf_bytes) > 25 * 1024 * 1024:
            raise ValueError("PDF is empty or exceeds 25 MiB")
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        if document.page_count > max_pages:
            raise ValueError("PDF exceeds the configured OCR page limit")
        pages: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(dpi=200, alpha=False)
            image_value = Image.open(BytesIO(pixmap.tobytes("png")))
            pages.append(pytesseract.image_to_string(image_value, lang="vie+eng").strip())
        document.close()
        content = "\n\n".join(pages)
        if len(content.strip()) < 40:
            raise ValueError("OCR produced too little text")
        offset = 0
        ranges = []
        for page_number, text_value in enumerate(pages, 1):
            if page_number > 1:
                offset += 2
            start = offset
            offset += len(text_value)
            ranges.append((page_number, start, offset))
        return {"content": content, "page_count": len(pages), "page_ranges": ranges,
                "engine": "tesseract-vie-eng"}


@app.local_entrypoint()
def smoke_test() -> None:
    result = BgeM3().embed.remote(
        ["Quy chế đào tạo của Học viện Ngân hàng."],
        "document",
    )
    print("modal_embedding=ok")
    print(f"model={result['model']}, vectors={result['count']}, dimensions={result['dimensions']}")
