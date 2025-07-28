import json
import os

def clean_json_file(input_file, output_file=None):
    """
    Clean a JSON file by removing duplicate keys and ensuring proper formatting.
    If output_file is None, overwrites the input file.
    """
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the JSON content
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return False
    
    # Remove duplicates by creating a new dictionary with unique keys
    cleaned_data = {}
    for key, value in data.items():
        # Use the first occurrence of each key
        if key not in cleaned_data:
            cleaned_data[key] = value
    
    # Write the cleaned data back to the file
    output_path = output_file or input_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
    
    return True

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one directory to the project root
    project_root = os.path.dirname(script_dir)
    # Define the input and output paths
    input_path = os.path.join(project_root, 'data', 'drug_reference.json')
    output_path = os.path.join(project_root, 'data', 'drug_reference_cleaned.json')
    
    print(f"Cleaning JSON file: {input_path}")
    if clean_json_file(input_path, output_path):
        print(f"Successfully cleaned JSON. Output saved to: {output_path}")
    else:
        print("Failed to clean JSON file.")
