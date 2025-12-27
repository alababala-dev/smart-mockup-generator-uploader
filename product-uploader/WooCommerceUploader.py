import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import os
import threading
import time
import requests
import json
import re
import base64
import io
from requests.auth import HTTPBasicAuth
from woocommerce import API

# ================= IMAGE PROCESSING (PILLOW) =================
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ================= USER CREDENTIALS (CLEANSED) =================
SITE_URL = "https://your-store-url.com"
CONSUMER_KEY = "YOUR_WC_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_WC_CONSUMER_SECRET"
WP_USERNAME = "your-admin-email@example.com"
WP_APP_PASSWORD = "YOUR_WP_APP_PASSWORD"

# ================= GROQ API CREDENTIALS (CLEANSED) =================
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.2-90b-vision-preview" 

# ================= COLOR MAPPING (RGB) =================
COLOR_MAP = {
    "Black": (0, 0, 0), "White": (255, 255, 255), "Gray": (128, 128, 128),
    "Silver": (192, 192, 192), "Red": (200, 0, 0), "Gold": (212, 175, 55),
    "Blue": (0, 0, 200)
}

# ================= CONFIGURATION =================
ALL_CATEGORIES = ["Abstract", "Animals", "Gaming", "Cars", "Nature", "Pop Art"]

FILES_CONFIG = {
    "Canvas": {
        "prefix": "Canvas Print",
        "main_file": "mockup-room-canvas.webp",
        "gallery_files": ["gallery-view-1.webp", "gallery-view-2.webp"],
        "var_map": {"Internal Frame": "mockup-room-canvas.webp", "Roll Only": "roll-view.webp"}
    },
    "Framed": {
        "prefix": "Framed Poster",
        "main_file": "mockup-room-framed.webp",
        "gallery_files": ["black-frame.webp", "white-frame.webp", "wood-frame.webp"],
        "var_map": {"Black": "black-frame.webp", "White": "white-frame.webp", "Wood": "wood-frame.webp"}
    }
}

# ================= PRICING EXAMPLES =================
# (Simplified for the cleansed template)
CANVAS_PRICES = {
    ('Internal Frame', '50X70 cm'): {'reg': '250', 'sale': '199'},
    ('Internal Frame', '70X100 cm'): {'reg': '400', 'sale': '329'},
}

class UploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Commerce Smart Product Uploader (Groq Vision)")
        self.root.geometry("650x850")
        self.site_categories_map = {} 

        tk.Label(root, text="WooCommerce Auto-Uploader", font=("Arial", 16, "bold")).pack(pady=10)

        # 1. Product Type
        frame_top = tk.LabelFrame(root, text="1. Product Type", font=("Arial", 10, "bold"), padx=10, pady=5)
        frame_top.pack(fill="x", padx=20, pady=5)
        self.type_var = tk.StringVar(value="Canvas")
        self.type_menu = ttk.Combobox(frame_top, textvariable=self.type_var, state="readonly", width=40)
        self.type_menu['values'] = ("Canvas", "Framed")
        self.type_menu.pack()

        # 2. Settings
        frame_settings = tk.LabelFrame(root, text="2. Settings", font=("Arial", 10, "bold"), padx=10, pady=5)
        frame_settings.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_settings, text="Start Model ID:").grid(row=0, column=0, sticky="e")
        self.entry_start_id = tk.Entry(frame_settings, width=15)
        self.entry_start_id.insert(0, "1001")
        self.entry_start_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.var_ai_keywords = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_settings, text="Enable AI Keyword Extraction (Groq)", variable=self.var_ai_keywords).grid(row=1, column=0, columnspan=2)

        # 3. Folder Selection
        self.folder_path = tk.StringVar()
        tk.Button(root, text="Select Master Folder", command=self.select_folder).pack(fill="x", padx=40, pady=15)
        self.lbl_folder = tk.Label(root, text="No folder selected", fg="gray")
        self.lbl_folder.pack()

        # Start Button
        tk.Button(root, text="START BATCH UPLOAD", command=self.start_thread, bg="#4CAF50", fg="white", font=("Arial", 12, "bold")).pack(fill="x", padx=40, pady=10)

        self.log_area = scrolledtext.ScrolledText(root, height=15, state='disabled')
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.lbl_folder.config(text=folder, fg="black")

    def start_thread(self):
        threading.Thread(target=self.run_upload, daemon=True).start()

    def upload_file(self, filepath, wp_auth):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as img_data:
            files = {'file': (filename, img_data, 'image/webp')}
            res = requests.post(f"{SITE_URL}/wp-json/wp/v2/media", files=files, auth=wp_auth)
        if res.status_code == 201: return res.json()['id']
        return None

    # ================= GROQ VISION LOGIC =================
    def extract_metadata_with_ai(self, folder_path, filename):
        target_file = os.path.join(folder_path, filename)
        if not os.path.exists(target_file) or not PIL_AVAILABLE: return [], ""
        
        try:
            with Image.open(target_file) as img:
                img.thumbnail((1024, 1024))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                encoded_string = base64.b64encode(buffer.read()).decode('utf-8')

            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt = "Identify the main colors and the primary subject of this image. Return JSON: {'colors': [], 'subject': ''}"

            payload = {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                ]}]
            }

            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()['choices'][0]['message']['content']
                # Basic cleaning of response
                data = data.replace("```json", "").replace("```", "").strip()
                result = json.loads(data)
                return result.get('colors', []), result.get('subject', "")
        except: pass
        return [], ""

    # ================= CORE UPLOAD PROCESS =================
    def run_upload(self):
        selected_mode = self.type_var.get()
        master_folder = self.folder_path.get()
        start_id = int(self.entry_start_id.get())
        
        wcapi = API(url=SITE_URL, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, version="wc/v3", timeout=60)
        wp_auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD.replace(" ", ""))
        
        subfolders = [f.path for f in os.scandir(master_folder) if f.is_dir()]
        subfolders.sort()

        current_id = start_id
        for product_folder in subfolders:
            self.log(f"\n[Processing] Folder: {os.path.basename(product_folder)}")
            config = FILES_CONFIG[selected_mode]
            
            # AI Metadata Analysis
            colors, subject = self.extract_metadata_with_ai(product_folder, config['main_file'])
            prod_name = f"{config['prefix']} - {subject} (Model {current_id})"
            
            # Upload Images
            main_id = self.upload_file(os.path.join(product_folder, config['main_file']), wp_auth)
            
            if main_id:
                # Create Product via WooCommerce API
                product_data = {
                    "name": prod_name,
                    "type": "variable",
                    "status": "publish",
                    "images": [{"id": main_id}],
                    "tags": [{"name": c} for c in colors],
                    "attributes": [
                        {"name": "Size", "visible": True, "variation": True, "options": ["50X70 cm", "70X100 cm"]}
                    ]
                }
                
                res = wcapi.post("products", product_data).json()
                if 'id' in res:
                    self.log(f"      [Success] Created Product ID: {res['id']}")
                    
                    # Create Variations logic would follow here...
            
            current_id += 1

        self.log("\n--- BATCH UPLOAD COMPLETE ---")

if __name__ == "__main__":
    root = tk.Tk()
    app = UploaderApp(root)
    root.mainloop()
