from constants import  ALLOWED_PDF_FORMAT, MAX_PAGES
import fitz  # PyMuPDF
from typing import List, Tuple


def is_pdf_truncated(file_bytes: bytes) -> bool:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return len(doc) > MAX_PAGES

def convert_pdf_to_image(filename: str, file_bytes: bytes) -> List[Tuple[str, bytes]]:
    """Convert PDF pages to images

    Args:
        filename (str): PDF file name
        file_bytes (bytes): PDF file in bytes
    Returns:
        List[Tuple[str, bytes]]: List of Tuple with filename and image bytes for each page
    """
    
    pages: List[Tuple[str, bytes]] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num, page in enumerate(doc):
        if page_num >= MAX_PAGES:
            break
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("jpg")
        pages.append((f"{filename[:-4]}_page_{page_num+1}.jpg", img_bytes))
    return pages


def read_uploaded_files(uploaded_files: List) -> List[Tuple[str, bytes]]:
    """Read uploaded files and convert PDFs to images if needed.

    Args:
        uploaded_files: List of uploaded files from Streamlit file uploader
    Returns:
        List[Tuple[str, bytes]]: List of Tuple with filename and file bytes
    """
    
    converted_files: List[Tuple[str, bytes]] = []
    for uploaded_file in uploaded_files: 

        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()   

        if uploaded_file.name.lower().endswith(tuple(ALLOWED_PDF_FORMAT)):
            converted_pdf = convert_pdf_to_image(uploaded_file.name, file_bytes)
            converted_files.extend(converted_pdf)
        else:
            converted_files.append((uploaded_file.name, file_bytes))
    return converted_files