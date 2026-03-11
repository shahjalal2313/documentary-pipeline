import json
import os

def extract_narration(json_path, output_txt_path):
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    narrations = []
    if 'chapters' in data:
        for chapter in data['chapters']:
            if 'narration' in chapter:
                narrations.append(chapter['narration'])
    
    script_text = "\n\n".join(narrations)

    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(script_text)
    
    print(f"Successfully extracted narration to {output_txt_path}")

if __name__ == "__main__":
    # Path to the specific WeWork JSON
    json_input = os.path.join('output', 'scripts', 'the_rise_and_fall_of_wework.json')
    # Output path
    txt_output = os.path.join('output', 'scripts', 'the_rise_and_fall_of_wework.txt')
    
    extract_narration(json_input, txt_output)
