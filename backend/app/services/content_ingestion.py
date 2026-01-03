from typing import Dict, List
import os
from openai import OpenAI
from pathlib import Path
import tempfile
from .document_processor import DocumentProcessor
from .vector_store import VectorStoreService


class ContentIngestionService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreService()

    async def transcribe_video(self, video_path: str) -> str:
        with open(video_path, "rb") as audio_file:
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcript

    async def process_and_ingest_video(
        self,
        video_path: str,
        creator_id: str,
        metadata: Dict = None
    ) -> Dict:
        transcript = await self.transcribe_video(video_path)

        metadata = metadata or {}
        metadata.update({
            "content_type": "video_transcript",
            "creator_id": creator_id,
            "source": metadata.get("title", Path(video_path).stem)
        })

        chunks = await self.doc_processor.process_transcript(
            text=transcript,
            metadata=metadata
        )

        result = await self.vector_store.add_documents(
            documents=chunks,
            creator_id=creator_id
        )

        return {
            **result,
            "transcript_length": len(transcript),
            "chunks_created": len(chunks)
        }

    async def process_and_ingest_pdf(
        self,
        pdf_path: str,
        creator_id: str,
        metadata: Dict = None
    ) -> Dict:
        metadata = metadata or {}
        metadata.update({
            "content_type": "pdf",
            "creator_id": creator_id,
            "source": metadata.get("title", Path(pdf_path).stem)
        })

        chunks = await self.doc_processor.process_pdf(
            file_path=pdf_path,
            metadata=metadata
        )

        result = await self.vector_store.add_documents(
            documents=chunks,
            creator_id=creator_id
        )

        return {
            **result,
            "chunks_created": len(chunks)
        }

    async def process_and_ingest_text(
        self,
        text_path: str,
        creator_id: str,
        metadata: Dict = None
    ) -> Dict:
        metadata = metadata or {}
        metadata.update({
            "content_type": "text",
            "creator_id": creator_id,
            "source": metadata.get("title", Path(text_path).stem)
        })

        chunks = await self.doc_processor.process_text(
            file_path=text_path,
            metadata=metadata
        )

        result = await self.vector_store.add_documents(
            documents=chunks,
            creator_id=creator_id
        )

        return {
            **result,
            "chunks_created": len(chunks)
        }

    async def ingest_content(
        self,
        file_path: str,
        content_type: str,
        creator_id: str,
        metadata: Dict = None
    ) -> Dict:
        if content_type == "video":
            return await self.process_and_ingest_video(file_path, creator_id, metadata)
        elif content_type == "pdf":
            return await self.process_and_ingest_pdf(file_path, creator_id, metadata)
        elif content_type == "text":
            return await self.process_and_ingest_text(file_path, creator_id, metadata)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
