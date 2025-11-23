"""
Example usage of TheConverter API
"""

import requests
import sys
from pathlib import Path


def detect_file(file_path: str):
    """Detect file type using the API"""
    url = "http://localhost:8000/detect"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Detection successful:")
        print(f"   Type: {result['detected_type']}")
        print(f"   Format: {result['detected_format']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Metadata: {result['metadata']}")
        print(f"   Suggested formats: {', '.join(result['suggested_formats'])}")
        return result
    else:
        print(f"❌ Detection failed: {response.text}")
        return None


def convert_file(file_path: str, output_format: str, quality: str = "high"):
    """Convert file using the API"""
    url = "http://localhost:8000/convert"
    
    output_filename = f"{Path(file_path).stem}_converted.{output_format}"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'output_format': output_format,
            'quality': quality
        }
        response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Conversion successful: {output_filename}")
        return output_filename
    else:
        print(f"❌ Conversion failed: {response.text}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python example.py <file_path> [output_format] [quality]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # First, detect the file
    print(f"\n🔍 Detecting file: {file_path}")
    detection = detect_file(file_path)
    
    if detection and len(sys.argv) >= 3:
        output_format = sys.argv[2]
        quality = sys.argv[3] if len(sys.argv) >= 4 else "high"
        
        print(f"\n🔄 Converting to {output_format} (quality: {quality})")
        convert_file(file_path, output_format, quality)
    
    print("\n✨ Done!")
