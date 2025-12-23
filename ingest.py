import os
import re
from typing import List, Dict, Any
import uuid
from pathlib import Path
from bs4 import BeautifulSoup
import markdown
from services.embedding_service import embedding_service
from services.vector_service import vector_service
from utils.chunking_utils import chunk_document, clean_text

def extract_title_from_content(content: str) -> str:
    """
    Extract title from markdown content (first heading)
    """
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()  # Remove '# ' prefix
        elif line.startswith('## '):
            return line[3:].strip()  # Remove '## ' prefix
    return "Untitled"

def process_markdown_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a markdown file and return chunks with metadata
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from content or use filename
    title = extract_title_from_content(content)
    if not title or title == "Untitled":
        title = Path(file_path).stem

    # Convert markdown to plain text for chunking
    html = markdown.markdown(content)
    soup = BeautifulSoup(html, 'html.parser')
    plain_text = soup.get_text()

    # Clean the text
    clean_content = clean_text(plain_text)

    # Extract metadata from file path and content
    # Convert to absolute path and get relative path from docs directory
    abs_path = os.path.abspath(file_path)
    docs_abs_path = os.path.abspath('../docs')
    relative_path = os.path.relpath(abs_path, docs_abs_path)
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file_path))

    # Try to extract chapter/section from path
    path_parts = relative_path.split('/')
    chapter = path_parts[0] if len(path_parts) > 1 else "General"
    section = Path(file_path).stem

    # Use the new chunking utilities
    chunks = chunk_document(
        content=plain_text,
        source_path=relative_path,
        document_id=document_id,
        title=title,
        chapter=chapter,
        section=section,
        chunk_method="tokens",
        max_tokens=500,
        overlap_tokens=50
    )

    return chunks

def scan_docs_directory(docs_dir: str = "../docs") -> List[Dict[str, Any]]:
    """
    Scan the docs directory for markdown files and process them
    """
    all_chunks = []

    if not os.path.exists(docs_dir):
        print(f"Directory {docs_dir} does not exist. Creating empty directory.")
        os.makedirs(docs_dir, exist_ok=True)
        return []

    # Find all markdown and mdx files
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.lower().endswith(('.md', '.mdx')):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                try:
                    chunks = process_markdown_file(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")

    print(f"Total chunks created: {len(all_chunks)}")
    return all_chunks

def ingest_documents(docs_dir: str = "../docs"):
    """
    Main function to ingest documents from the docs directory
    """
    print("Starting document ingestion process...")

    # Scan and process all documents
    chunks = scan_docs_directory(docs_dir)

    if not chunks:
        print("No documents found to process.")
        return

    print(f"Processing {len(chunks)} chunks...")

    # Store chunks in vector database
    vector_service.store_chunks(chunks)

    print("Document ingestion completed successfully!")

if __name__ == "__main__":
    # Default to docs directory, but allow override
    docs_path = os.getenv("DOCS_PATH", "docs")
    ingest_documents(docs_path)