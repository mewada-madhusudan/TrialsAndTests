import functools
import timeout_decorator
from cachetools import cached, TTLCache

class OptimizedDocumentProcessor:
    def __init__(self, cache_size=100, cache_ttl=3600):
        """Initialize with caching and timeout support"""
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
    
    @cached(cache)
    @timeout_decorator.timeout(60)  # 60-second timeout
    def process_document(self, file_path: str) -> str:
        """Enhanced document processing with caching and timeout"""
        file_path = file_path.strip()
        ext = os.path.splitext(file_path)[1].lower()
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return ""
        
        try:
            # More robust extraction attempts
            extractors = {
                '.pdf': self.extract_from_pdf_robust,
                '.docx': self.extract_from_docx_robust,
                '.jpg': self.extract_from_image_robust,
                '.jpeg': self.extract_from_image_robust,
                '.png': self.extract_from_image_robust
            }
            
            extractor = extractors.get(ext, lambda x: "")
            return extractor(file_path)
        
        except Exception as e:
            logger.error(f"Processing error for {file_path}: {e}")
            return ""
    
    def extract_from_pdf_robust(self, file_path):
        """More robust PDF extraction"""
        try:
            # Try multiple extraction methods
            methods = [
                self.extract_from_pdf,  # Original method
                self.optimized_ocr_pdf,  # Optimized OCR method
                self.tesseract_pdf_extraction
            ]
            
            for method in methods:
                text = method(file_path)
                if text.strip():
                    return text
            
            return ""
        except Exception as e:
            logger.error(f"Robust PDF extraction failed: {e}")
            return ""
