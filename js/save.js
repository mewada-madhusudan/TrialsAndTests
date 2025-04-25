import json
import os
import sys
from urllib.parse import urlparse
import requests
from urllib.request import url2pathname

def process_sourcemap(map_file_path, output_dir=None):
    """
    Process a JavaScript source map file to rebuild original source files.
    
    Args:
        map_file_path (str): Path to the source map (.map) file
        output_dir (str, optional): Directory to save reconstructed files. Defaults to 'reconstructed_sources'.
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = 'reconstructed_sources'
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read the source map file
    try:
        with open(map_file_path, 'r', encoding='utf-8') as f:
            sourcemap_data = json.load(f)
    except Exception as e:
        print(f"Error reading source map file: {e}")
        return
    
    # Extract source file names
    source_files = sourcemap_data.get('sources', [])
    source_contents = sourcemap_data.get('sourcesContent', [])
    
    # Base directory of the source map file for relative path resolution
    base_dir = os.path.dirname(os.path.abspath(map_file_path))
    
    # Process each source file
    for i, source_file in enumerate(source_files):
        print(f"Processing source file: {source_file}")
        
        # If sourcesContent is provided in the map file, use it directly
        if source_contents and i < len(source_contents) and source_contents[i] is not None:
            file_content = source_contents[i]
            print(f"Using embedded content for {source_file}")
        else:
            # Otherwise, try to find the file locally or fetch from URL
            file_content = get_source_content(source_file, base_dir)
            if file_content is None:
                print(f"Source file not found: {source_file}")
                continue
        
        # Determine output file path
        if source_file.startswith('http://') or source_file.startswith('https://'):
            # For URLs, extract the filename part
            parsed_url = urlparse(source_file)
            file_name = os.path.basename(parsed_url.path)
        else:
            # For relative paths, use the path as is
            file_name = source_file
        
        # Remove any leading slashes or dots
        file_name = file_name.lstrip('./\\')
        
        # Create subdirectories if needed
        file_dir = os.path.dirname(file_name)
        if file_dir:
            os.makedirs(os.path.join(output_dir, file_dir), exist_ok=True)
        
        # Write the content to the output file
        output_path = os.path.join(output_dir, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"Saved: {output_path}")

def get_source_content(source_file, base_dir):
    """
    Attempt to get the content of a source file, either locally or from a URL.
    
    Args:
        source_file (str): Path or URL to the source file
        base_dir (str): Base directory for resolving relative paths
        
    Returns:
        str or None: The file content if found, None otherwise
    """
    # Check if it's a URL
    if source_file.startswith('http://') or source_file.startswith('https://'):
        try:
            response = requests.get(source_file)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error fetching URL {source_file}: {e}")
    else:
        # Try to find the file locally
        # First, check relative to base_dir
        local_path = os.path.normpath(os.path.join(base_dir, source_file))
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Then, check in a "sources" subdirectory
        sources_path = os.path.join(base_dir, 'sources', source_file)
        if os.path.exists(sources_path):
            with open(sources_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    return None

if __name__ == "__main__":
    # Command line arguments handling
    if len(sys.argv) < 2:
        print("Usage: python sourcemap_rebuild.py <path_to_map_file> [output_directory]")
        sys.exit(1)
    
    map_file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_sourcemap(map_file_path, output_dir)
