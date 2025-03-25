import multiprocessing
from functools import partial
import cv2
import numpy as np

def preprocess_image(image, resize=False):
    """Preprocess image for better OCR performance"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Optional: Resize if image is too large
    if resize and (image.shape[0] > 2000 or image.shape[1] > 2000):
        scale_factor = min(2000/image.shape[0], 2000/image.shape[1])
        thresh = cv2.resize(thresh, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
    
    return thresh

def process_page_ocr(page, lang='eng'):
    """Process a single page with OCR"""
    try:
        # Convert PIL to numpy array
        page_np = np.array(page)
        
        # Preprocess image
        preprocessed = preprocess_image(page_np, resize=True)
        
        # Convert back to PIL for pytesseract
        pil_img = Image.fromarray(preprocessed)
        
        # Apply OCR with improved configuration
        text = pytesseract.image_to_string(
            pil_img, 
            lang=lang,
            config='--oem 3 --psm 6'  # Improved OCR engine mode and page segmentation mode
        )
        return text
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        return ""

def optimized_ocr_pdf(file_path: str, max_workers=None) -> str:
    """Optimized OCR processing with multiprocessing"""
    try:
        from pdf2image import convert_from_path
        
        # Determine max workers based on CPU cores
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() - 2)
        
        # Convert PDF with lower DPI
        pages = convert_from_path(file_path, 200)  # Reduced DPI
        
        # Use multiprocessing for parallel OCR
        with multiprocessing.Pool(processes=max_workers) as pool:
            text_results = pool.map(process_page_ocr, pages)
        
        return '\n'.join(text_results)
    except Exception as e:
        logger.error(f"Optimized OCR error for {file_path}: {e}")
        return ""
