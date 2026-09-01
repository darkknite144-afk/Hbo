import os
import json
import time
import re
from playwright.sync_api import sync_playwright

# Configuration
TOTAL_BATCHES = 12       # 12 Batches * 50 Scenes = 600 Scenes (~1 Hour Video)
SCENES_PER_BATCH = 50
TARGET_URL = "https://chat.deepseek.com"  # Ya aistudio.google.com
SESSION_DIR = "./chrome_user_session"
OUTPUT_DIR = "output"

# Prompt Template
PROMPT_TEMPLATE = """
[ROLE: Elite Korean Webtoon/Manhwa Screenwriter & YouTube Storyteller]
Genre: Solo Leveling / System / Dark Fantasy / Reincarnation
Art Anchor: "manhwa webtoon style, solo leveling art, dynamic lighting, sharp lineart, 16:9 widescreen"

Batch Number: {batch_no} (Generate Scenes {start_scene} to {end_scene})
Continuity Context: {continuity_buffer}

RULES:
1. NARRATION: Fast-paced conversational Hindi/Hinglish YouTube recap style (10-18 words per scene, 3-5 seconds pacing).
2. IMAGE PROMPT: Detailed 16:9 visual prompt including the Art Anchor for each scene.
3. OUTPUT: Output MUST be valid raw JSON only.

JSON Format:
{{
  "batch": {batch_no},
  "scenes": [
    {{
      "id": {start_scene},
      "narration": "...",
      "image_prompt": "..."
    }}
  ],
  "next_scene_buffer": "..."
}}
"""

def extract_json(raw_text):
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
    return None

def save_to_text_files(scenes, episode_no=1):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    script_file = os.path.join(OUTPUT_DIR, f"full_narration_script_ep{episode_no}.txt")
    prompts_file = os.path.join(OUTPUT_DIR, f"google_flow_prompts_ep{episode_no}.txt")
    
    with open(script_file, "a", encoding="utf-8") as sf, open(prompts_file, "a", encoding="utf-8") as pf:
        for sc in scenes:
            scene_id = sc.get("id", "0")
            narration = sc.get("narration", "").strip()
            prompt = sc.get("image_prompt", "").strip()
            
            # Write Clean Voiceover Script
            sf.write(f"[{scene_id}] {narration}\n\n")
            
            # Write Clean Image Prompt (Direct Google Flow ready)
            pf.write(f"{prompt}\n")

def run_agent():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current_buffer = "Story starts fresh. MC enters an unknown low-rank dungeon."
    
    print("\n Launching Browser Agent...")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            channel="chrome",
            args=["--start-maximized"]
        )
        
        page = browser.new_page()
        page.goto(TARGET_URL)
        
        input("\n[!] Browser me account login karein, fir yahan terminal me ENTER dabayein...")
        
        for batch in range(1, TOTAL_BATCHES + 1):
            start_scene = (batch - 1) * SCENES_PER_BATCH + 1
            end_scene = batch * SCENES_PER_BATCH
            
            formatted_prompt = PROMPT_TEMPLATE.format(
                batch_no=batch,
                start_scene=start_scene,
                end_scene=end_scene,
                continuity_buffer=current_buffer
            )
            
            print(f"\n Sending Prompt: Batch {batch}/{TOTAL_BATCHES} (Scenes {start_scene}-{end_scene})...")
            
            # Focus chat input
            box = page.locator("textarea, [contenteditable='true']").first
            box.click()
            box.fill(formatted_prompt)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("⏳ AI is writing... Waiting for response to complete...")
            time.sleep(8)
            
            # Wait until generation finishes
            while True:
                stop_btn = page.locator("button:has-text('Stop'), [aria-label='Stop']").count()
                if stop_btn == 0:
                    break
                time.sleep(3)
            
            # Extract latest response
            messages = page.locator(".markdown, .prose, .message-content").all()
            if messages:
                raw_response = messages[-1].inner_text()
                parsed = extract_json(raw_response)
                
                if parsed and "scenes" in parsed:
                    scenes = parsed["scenes"]
                    save_to_text_files(scenes, episode_no=1)
                    
                    if "next_scene_buffer" in parsed:
                        current_buffer = parsed["next_scene_buffer"]
                    print(f" Batch {batch} successfully saved to text files! ({len(scenes)} scenes added)")
                else:
                    # Fallback log in case JSON parsing needs check
                    raw_log_path = os.path.join(OUTPUT_DIR, f"raw_batch_{batch}.txt")
                    with open(raw_log_path, "w", encoding="utf-8") as f:
                        f.write(raw_response)
                    print(f"⚠️ Batch {batch} JSON auto-parse issue. Saved to {raw_log_path}")
            
            time.sleep(3)
            
        print("\n All batches completed! Check the 'output' folder for your two files.")
        browser.close()

if __name__ == "__main__":
    run_agent()
