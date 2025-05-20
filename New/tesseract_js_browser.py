"""
Using Tesseract.js in Python without Node.js
"""

# Approach 1: Using PyExecJS to run JavaScript code directly in Python
# pip install PyExecJS

import execjs
import json
import base64
from PIL import Image
import io
import os
import tempfile

class TesseractJSBrowser:
    """
    Use Tesseract.js in Python without Node.js using PyExecJS
    """
    def __init__(self):
        # Check if PyExecJS is available
        try:
            import execjs
        except ImportError:
            raise ImportError("PyExecJS is not installed. Install it using 'pip install PyExecJS'")
        
        # Load the Tesseract.js library
        self.tesseract_js_code = self._get_tesseract_js_code()
        
        # Create JavaScript context
        self.ctx = execjs.compile(self.tesseract_js_code)
        
    def _get_tesseract_js_code(self):
        """Get the Tesseract.js library code."""
        # You can either:
        # 1. Download the tesseract.js file and load it from disk
        # 2. Include a minified version directly in this function
        
        # Option 1: Load from a local file if you've downloaded it
        # tesseract_js_path = "path/to/tesseract.min.js"
        # if os.path.exists(tesseract_js_path):
        #     with open(tesseract_js_path, 'r') as f:
        #         return f.read()
        
        # Option 2: Use the CDN version (this creates a script that will load it)
        return """
        // This is a wrapper to load and use Tesseract.js
        
        // Create a function to convert base64 image to text
        function recognizeText(base64Image, lang) {
            // This is a simplified version for demonstration
            // In reality, you need the full Tesseract.js library loaded
            
            // The actual implementation would use:
            // return Tesseract.recognize(base64Image, lang, {})
            //   .then(result => {
            //     return JSON.stringify({
            //       text: result.data.text,
            //       confidence: result.data.confidence
            //     });
            //   });
            
            // For now, this is just a placeholder that shows the API pattern
            return JSON.stringify({
                error: "This is a placeholder. You need to include the full Tesseract.js library."
            });
        }
        """
    
    def recognize_image(self, image_path, lang='eng'):
        """
        Recognize text in an image using Tesseract.js.
        
        Args:
            image_path (str or PIL.Image): Path to the image file or PIL Image object.
            lang (str): Language for OCR.
            
        Returns:
            dict: OCR result containing text and confidence.
        """
        # Convert image to base64
        if isinstance(image_path, str):
            image = Image.open(image_path)
        else:
            image = image_path
            
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Call the JavaScript function
        result_json = self.ctx.call("recognizeText", f"data:image/png;base64,{img_base64}", lang)
        
        # Parse the result
        try:
            return json.loads(result_json)
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON from JavaScript result."}


# Approach 2: Using a Simple Flask Web Server to serve a browser-based OCR

from flask import Flask, render_template_string, request, jsonify
import webbrowser
import threading
import time
import requests

class TesseractJSWebServer:
    """
    Use Tesseract.js in Python through a local web server that uses the browser's JavaScript engine.
    """
    def __init__(self, port=5000):
        self.port = port
        self.app = Flask(__name__)
        self.result = None
        self.processing = False
        self.ready = False
        
        # Define routes
        @self.app.route('/')
        def home():
            return render_template_string(self._get_html_template())
        
        @self.app.route('/process', methods=['POST'])
        def process():
            data = request.json
            self.result = data
            self.processing = False
            return jsonify({"status": "success"})
            
        @self.app.route('/status')
        def status():
            return jsonify({"ready": self.ready})
        
        # Start the server in a separate thread
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Open the browser
        webbrowser.open(f'http://localhost:{self.port}')
        
        # Wait for the page to be ready
        print("Starting web server for Tesseract.js...")
        self._wait_for_ready()
        print("Tesseract.js web service ready!")
        
    def _run_server(self):
        """Run the Flask server."""
        self.app.run(port=self.port, threaded=True)
        
    def _wait_for_ready(self):
        """Wait for the web page to signal it's ready."""
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while not self.ready and time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://localhost:{self.port}/status')
                if response.status_code == 200:
                    data = response.json()
                    self.ready = data.get('ready', False)
                    if self.ready:
                        break
            except:
                pass
            time.sleep(0.5)
            
        if not self.ready:
            print("Warning: Timed out waiting for Tesseract.js to load in browser. Try refreshing the page.")
    
    def _get_html_template(self):
        """Get the HTML template for the Tesseract.js web page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tesseract.js OCR</title>
            <script src='https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js'></script>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                #progressBar { width: 100%; height: 20px; background-color: #f3f3f3; border-radius: 4px; margin: 10px 0; }
                #progressFill { height: 100%; width: 0; background-color: #4CAF50; border-radius: 4px; }
                #result { white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #ddd; }
                .hidden { display: none; }
            </style>
        </head>
        <body>
            <h1>Tesseract.js OCR</h1>
            <p id="status">Loading Tesseract.js...</p>
            <div id="imageContainer" class="hidden">
                <img id="previewImage" style="max-width: 100%; max-height: 400px; margin: 20px 0;" />
            </div>
            <div id="progressContainer" class="hidden">
                <div id="progressBar"><div id="progressFill"></div></div>
                <div id="progressText">Processing: 0%</div>
            </div>
            <pre id="result" class="hidden"></pre>
            
            <script>
                // Notify server when Tesseract.js is ready
                window.onload = async function() {
                    try {
                        await Tesseract.load();
                        document.getElementById('status').textContent = 'Tesseract.js is ready. Waiting for images from Python...';
                        fetch('/status', {
                            method: 'GET'
                        });
                        sendReadyStatus();
                    } catch (error) {
                        document.getElementById('status').textContent = 'Error loading Tesseract.js: ' + error.message;
                    }
                };
                
                function sendReadyStatus() {
                    fetch('/status', {
                        method: 'GET'
                    });
                    
                    // Check if a message handler exists
                    if (window.onTesseractReady) {
                        window.onTesseractReady();
                    }
                }
                
                // Function to process an image
                async function processImage(imageData, lang) {
                    try {
                        // Display the image
                        document.getElementById('imageContainer').classList.remove('hidden');
                        document.getElementById('previewImage').src = imageData;
                        
                        // Show progress bar
                        document.getElementById('progressContainer').classList.remove('hidden');
                        document.getElementById('result').classList.add('hidden');
                        
                        // Perform OCR
                        const result = await Tesseract.recognize(imageData, lang, {
                            logger: progress => {
                                if (progress.status === 'recognizing text') {
                                    const percent = Math.round(progress.progress * 100);
                                    document.getElementById('progressFill').style.width = percent + '%';
                                    document.getElementById('progressText').textContent = 'Processing: ' + percent + '%';
                                }
                            }
                        });
                        
                        // Display the result
                        document.getElementById('result').textContent = result.data.text;
                        document.getElementById('result').classList.remove('hidden');
                        
                        // Send the result back to the server
                        await fetch('/process', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                text: result.data.text,
                                confidence: result.data.confidence,
                                words: result.data.words,
                                // Add other data as needed
                            })
                        });
                        
                        return true;
                    } catch (error) {
                        document.getElementById('status').textContent = 'Error: ' + error.message;
                        return false;
                    }
                }
                
                // Add a global function that Python can call
                window.processImageFromPython = processImage;
                window.onTesseractReady = function() {
                    fetch('/status', {
                        method: 'GET'
                    });
                };
            </script>
        </body>
        </html>
        """
    
    def recognize_image(self, image_path, lang='eng'):
        """
        Recognize text in an image using Tesseract.js via web browser.
        
        Args:
            image_path (str or PIL.Image): Path to the image file or PIL Image object.
            lang (str): Language for OCR.
            
        Returns:
            dict: OCR result containing text and confidence.
        """
        # Reset result and set processing flag
        self.result = None
        self.processing = True
        
        # Convert image to base64
        if isinstance(image_path, str):
            image = Image.open(image_path)
        else:
            image = image_path
            
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        img_data_url = f"data:image/png;base64,{img_base64}"
        
        # Use JavaScript in browser to process the image
        # TODO: Implement a way to send the image to the browser and trigger processing
        
        # Wait for processing to complete
        timeout = 60  # 60 seconds timeout
        start_time = time.time()
        
        while self.processing and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        if self.processing:
            return {"error": "Processing timed out"}
            
        return self.result if self.result else {"error": "Failed to process image"}


# Approach 3: Using HTML file with Tesseract.js (simplest approach)

class TesseractJSHTML:
    """
    Use Tesseract.js by creating an HTML file that can be opened in a browser
    """
    def __init__(self, output_dir=None):
        """
        Initialize the TesseractJSHTML class.
        
        Args:
            output_dir (str): Directory to save the HTML file and image. 
                             If None, a temporary directory is used.
        """
        self.output_dir = output_dir or tempfile.mkdtemp()
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_html(self, image_path, output_html=None, lang='eng'):
        """
        Create an HTML file that uses Tesseract.js to perform OCR on the image.
        
        Args:
            image_path (str or PIL.Image): Path to the image file or PIL Image object.
            output_html (str): Path to save the HTML file. If None, a default path is used.
            lang (str): Language for OCR.
            
        Returns:
            str: Path to the created HTML file.
        """
        # Save image if it's a PIL Image
        if isinstance(image_path, Image.Image):
            img_filename = os.path.join(self.output_dir, 'ocr_image.png')
            image_path.save(img_filename)
        else:
            # Copy the image to the output directory
            img_filename = os.path.join(self.output_dir, os.path.basename(image_path))
            with open(image_path, 'rb') as src, open(img_filename, 'wb') as dst:
                dst.write(src.read())
                
        # Get relative path for the HTML file
        img_rel_path = os.path.basename(img_filename)
        
        # Create the HTML file
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tesseract.js OCR</title>
            <script src='https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js'></script>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                #progressBar {{ width: 100%; height: 20px; background-color: #f3f3f3; border-radius: 4px; margin: 10px 0; }}
                #progressFill {{ height: 100%; width: 0; background-color: #4CAF50; border-radius: 4px; }}
                #result {{ white-space: pre-wrap; background: #f9f9f9; padding: 10px; border: 1px solid #ddd; }}
                .hidden {{ display: none; }}
                textarea {{ width: 100%; height: 200px; }}
            </style>
        </head>
        <body>
            <h1>Tesseract.js OCR</h1>
            <p>Processing image: {img_rel_path}</p>
            <div>
                <img id="image" src="{img_rel_path}" style="max-width: 100%; max-height: 400px; margin: 20px 0;" />
            </div>
            <div id="progressContainer">
                <div id="progressBar"><div id="progressFill"></div></div>
                <div id="progressText">Loading Tesseract.js...</div>
            </div>
            <h2>Extracted Text:</h2>
            <pre id="result" class="hidden"></pre>
            <h2>Raw OCR Data (for copying back to Python):</h2>
            <textarea id="jsonResult"></textarea>
            
            <script>
                // Process the image when the page loads
                window.onload = async function() {{
                    try {{
                        document.getElementById('progressText').textContent = 'Initializing Tesseract.js...';
                        
                        // Process the image
                        const worker = await Tesseract.createWorker('{lang}');
                        
                        // Set up progress tracking
                        worker.setProgressHandler(progress => {{
                            if (progress.status === 'recognizing text') {{
                                const percent = Math.round(progress.progress * 100);
                                document.getElementById('progressFill').style.width = percent + '%';
                                document.getElementById('progressText').textContent = 'Processing: ' + percent + '%';
                            }} else {{
                                document.getElementById('progressText').textContent = progress.status;
                            }}
                        }});
                        
                        // Perform OCR
                        document.getElementById('progressText').textContent = 'Starting OCR process...';
                        const result = await worker.recognize(document.getElementById('image'));
                        
                        // Display the results
                        document.getElementById('result').textContent = result.data.text;
                        document.getElementById('result').classList.remove('hidden');
                        document.getElementById('jsonResult').value = JSON.stringify(result.data, null, 2);
                        
                        // Clean up
                        await worker.terminate();
                        document.getElementById('progressText').textContent = 'OCR complete!';
                        
                    }} catch (error) {{
                        document.getElementById('progressText').textContent = 'Error: ' + error.message;
                        console.error(error);
                    }}
                }};
            </script>
        </body>
        </html>
        """
        
        # Save the HTML file
        output_html = output_html or os.path.join(self.output_dir, 'tesseract_ocr.html')
        with open(output_html, 'w') as f:
            f.write(html_content)
            
        print(f"HTML file created at: {output_html}")
        print(f"Open this file in your browser to perform OCR.")
        print(f"After processing, copy the JSON result from the text area back to your Python script.")
        
        # Try to open the file in the default browser
        try:
            webbrowser.open(f'file://{os.path.abspath(output_html)}')
        except:
            pass
            
        return output_html


# Example usage
if __name__ == "__main__":
    # Choose one of the approaches:
    
    # Example 1: PyExecJS approach (note: requires additional setup)
    # ocr = TesseractJSBrowser()
    # result = ocr.recognize_image("sample_image.png")
    # print(result)
    
    # Example 2: Web server approach
    # ocr = TesseractJSWebServer()
    # result = ocr.recognize_image("sample_image.png")
    # print(result)
    
    # Example 3: HTML file approach (simplest)
    ocr = TesseractJSHTML()
    html_path = ocr.create_html("sample_image.png")
    print(f"Open {html_path} in your browser to process the image")
    
    # After the browser processes the image, you would manually copy the JSON result
    # from the browser back to your Python script for further processing
