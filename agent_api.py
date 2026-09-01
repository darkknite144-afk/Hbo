import os
import json
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

TOTAL_BATCHES = 12
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROMPT_TEMPLATE = """
[ROLE: Elite Korean Webtoon/Manhwa Screenwriter]
Title: Shadow Monarch Rebirth
Style Anchor: "manhwa webtoon style, solo leveling art, dynamic lighting, 16:9 widescreen"

Batch Number: {batch} (Scenes {start} to {end})
Context: {buffer}

Output ONLY valid JSON.
Format: {{"scenes": [{{"id": {start}, "narration": "...", "image_prompt": "..."}}], "next_scene_buffer": "..."}}
"""

def run_github_agent():
    current_buffer = "Story starts fresh. MC enters an E-Rank dungeon."
    
    script_file = os.path.join(OUTPUT_DIR, "narration_script.txt")
    prompts_file = os.path.join(OUTPUT_DIR, "google_flow_prompts.txt")
    
    for batch in range(1, TOTAL_BATCHES + 1):
        start_scene = (batch - 1) * 50 + 1
        end_scene = batch * 50
        
        print(f"Generating Batch {batch}...")
        payload = {
            "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(batch=batch, start=start_scene, end=end_scene, buffer=current_buffer)}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        response = requests.post(URL, json=payload).json()
        
        try:
            raw_text = response['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(raw_text)
            
            with open(script_file, "a", encoding="utf-8") as sf, open(prompts_file, "a", encoding="utf-8") as pf:
                for sc in data.get("scenes", []):
                    sf.write(f"[{sc['id']}] {sc['narration']}\n\n")
                    pf.write(f"{sc['image_prompt']}\n")
            
            current_buffer = data.get("next_scene_buffer", current_buffer)
        except Exception as e:
            print(f"Error on batch {batch}: {e}")

if __name__ == "__main__":
    run_github_agent()
