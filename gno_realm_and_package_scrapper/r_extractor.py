from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import sys
from pathlib import Path
import time
import requests
import base64
from urllib.parse import urlparse
from dotenv import load_dotenv
from gno_realm_and_package_scrapper import get_artifacts_dir
from openai import OpenAI

# Load .env file at the start of the file
load_dotenv()

REALMS_URL = "https://github.com/gnolang/gno/tree/master/examples/gno.land/r"

def extract_github_content() -> dict[str, str]:
    """
    Extract content from all .md files in Gno docs repository including subfolders
    
    Returns:
        Dictionary with file paths as keys and their content as values
    """
    results = {}
    
    # Parse GitHub URL
    parts = urlparse(REALMS_URL).path.split('/')
    owner = "gnolang"
    repo = "gno"
    branch = "master"
    base_path = "examples/gno.land/r"
    
    # GitHub API URL for recursive tree listing
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    
    # Add GitHub token if available
    headers = {}
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        # Get full repository tree (including all subfolders)
        print("Fetching repository structure...")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        tree = response.json()

        # Find all .gno files in docs folder and subfolders
        gno_files = [
            item for item in tree['tree']
            if item['type'] == 'blob' 
            and item['path'].startswith(base_path) 
            and item['path'].endswith('.gno')
        ]
        
        print(f"Found {len(gno_files)} .gno files in repository")

        # Filter out test files
        gno_files = [item for item in gno_files if "test" not in item['path']]

        print(f"After removing test files, {len(gno_files)} files left")

        
        # Get content of each .gno file
        for item in gno_files:
            try:
                # Get file content
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{item['path']}?ref={branch}"
                file_response = requests.get(file_url, headers=headers)
                file_response.raise_for_status()
                content = base64.b64decode(file_response.json()['content']).decode('utf-8')
                
                # Skip files with less than 50 characters
                if len(content) < 50:
                    print(f"Skipping {item['path']} (less than 50 characters)")
                    continue  # Skip to the next file
                
                # Store relative path and content
                relative_path = item['path'][len(base_path):].lstrip('/')
                parent_folder = str(Path(relative_path).parent)
                
                # Combine content by parent folder
                if parent_folder not in results:
                    results[parent_folder] = (parent_folder if parent_folder != '.' else 'root', content)
                else:   
                    # Append content to existing entry
                    results[parent_folder] = (parent_folder, results[parent_folder][1] + "\n" + content)
                    
                print(f"Retrieved: {item['path']}")
                time.sleep(1)
                
            except Exception as e:
                print(f"Error retrieving {item['path']}: {str(e)}", file=sys.stderr)
                continue
                
    except Exception as e:
        print(f"Error accessing GitHub: {str(e)}", file=sys.stderr)
    
    print(f"Got {len(results)} artifacts")
    return results

def main():
    # Get script-specific artifacts directory
    artifacts_dir = get_artifacts_dir('realm_extractor')
    
    try:
        print(f"Starting extraction from {REALMS_URL}")
        gno_contents = extract_github_content()
        
        if not gno_contents:
            print("No .gno files found.")
            return
        
        # Generate timestamp for the folder
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_dir = os.path.join(artifacts_dir, f"gno_docs_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Sort files by folder for better organization
        sorted_files = sorted(gno_contents.items(), key=lambda x: (x[1][0], x[0]))
        
        # Create index file with descriptions of the realms
        index_file = os.path.join(output_dir, "realms_index.txt")
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(f"Found {len(gno_contents)} .gno files from Gno documentation\n")
            f.write(f"Source: https://gno.land/r\n")
            f.write("-" * 80 + "\n\n")
            f.write("File Name | Description\n")
            f.write("-" * 80 + "\n")
            
            client = OpenAI()
            
            for file_path, (folder, content) in sorted_files:
                print(f"Analyzing: {file_path}")
                try:
                    # Query ChatGPT for description
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a technical documentation analyzer. Provide a concise description of the REALM's functionality, summarizing its main purpose and key features. Do not use ; or | characters!"},
                            {"role": "user", "content": content}
                        ],
                        temperature=0.1
                    )
                    
                    # Extract description from response
                    summary = response.choices[0].message.content.strip()
                    
                    # Use the same safe filename format
                    safe_filename = file_path.replace('/', '_')
                    
                    # Write to index using the safe filename
                    f.write(f"{safe_filename} | {summary};\n")
                    
                    # Add a small delay to respect rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
                    f.write(f"{safe_filename} | Error extracting keywords\n")
        
        print(f"Content has been written to {output_dir}")
        print(f"Total files extracted: {len(gno_contents)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
