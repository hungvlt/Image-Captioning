import os
import pandas as pd
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

# Configuration
# "large" is stronger/smarter than "base", but slightly slower.
MODEL_ID = "Salesforce/blip-image-captioning-large" 
CSV_FILE = 'image_captions.csv'
ROOT_DIR = 'images'

def create_captioned_dataset():
    # 1. Check for existing data to avoid re-doing work
    processed_paths = set()
    if os.path.exists(CSV_FILE):
        print(f"Found existing {CSV_FILE}. Loading processed images...")
        try:
            existing_df = pd.read_csv(CSV_FILE)
            # Create a set of paths we have already done
            if 'image_path' in existing_df.columns:
                processed_paths = set(existing_df['image_path'].tolist())
            print(f"Skipping {len(processed_paths)} images already in database.")
        except Exception as e:
            print(f"Error reading existing CSV: {e}. Starting fresh.")

    # 2. Load the Stronger Model
    print(f"Loading Stronger Model: {MODEL_ID}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    try:
        processor = BlipProcessor.from_pretrained(MODEL_ID)
        model = BlipForConditionalGeneration.from_pretrained(MODEL_ID).to(device)
    except Exception as e:
        print(f"Error loading model. Make sure you have internet access: {e}")
        return

    print(f"Model loaded on {device}!")

    if not os.path.isdir(ROOT_DIR):
        print(f"Error: Directory '{ROOT_DIR}' not found.")
        return

    new_data = []
    
    # 3. Walk through folders
    print("Scanning for new images...")
    for label in os.listdir(ROOT_DIR):
        label_dir = os.path.join(ROOT_DIR, label)
        if os.path.isdir(label_dir):
            
            for filename in os.listdir(label_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_path = os.path.join(label_dir, filename)
                    
                    # --- THE FIX: Skip if we already did this one ---
                    if image_path in processed_paths:
                        continue
                    
                    try:
                        # Generate Caption
                        raw_image = Image.open(image_path).convert('RGB')
                        
                        # "conditional" captioning: You can add text="a photo of" to guide it if needed
                        inputs = processor(raw_image, return_tensors="pt").to(device)
                        
                        # Generate text (parameters tuned for better quality)
                        out = model.generate(
                            **inputs, 
                            max_new_tokens=70,  # Allow slightly longer descriptions
                            min_length=20,      # Force it to be more descriptive
                            num_beams=5         # "Beam search" finds better sentences than greedy search
                        )
                        caption_text = processor.decode(out[0], skip_special_tokens=True)
                        
                        print(f"New: {filename} -> {caption_text}")
                        
                        # Store in list
                        new_data.append({
                            'image_path': image_path, 
                            'folder_label': label,
                            'caption': caption_text
                        })
                        
                    except Exception as e:
                        print(f"Could not caption {filename}: {e}")

    # 4. Save incrementally
    if new_data:
        new_df = pd.DataFrame(new_data)
        
        # If file doesn't exist, write header. If it does, append without header.
        header_mode = not os.path.exists(CSV_FILE)
        new_df.to_csv(CSV_FILE, mode='a', header=header_mode, index=False)
        
        print(f"\nSuccess! Appended {len(new_df)} new images to '{CSV_FILE}'")
    else:
        print("\nNo new images found to process.")

if __name__ == '__main__':
    create_captioned_dataset()