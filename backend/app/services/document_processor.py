from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
import os


class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def process_pdf(self, file_path: str, metadata: Dict = None) -> List[Document]:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)

        chunks = self.text_splitter.split_documents(documents)
        return chunks

    async def process_text(self, file_path: str, metadata: Dict = None) -> List[Document]:
        loader = TextLoader(file_path)
        documents = loader.load()

        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)

        chunks = self.text_splitter.split_documents(documents)
        return chunks

    async def process_transcript(self, text: str, metadata: Dict = None) -> List[Document]:
        document = Document(page_content=text, metadata=metadata or {})
        chunks = self.text_splitter.split_documents([document])
        return chunks
