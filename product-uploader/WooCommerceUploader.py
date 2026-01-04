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

# ================= USER CREDENTIALS =================
SITE_URL = "https://YOUR-WEBSITE.co.il"
CONSUMER_KEY = "ck_X"
CONSUMER_SECRET = "cs_X"
WP_USERNAME = "example@mail.com"
WP_APP_PASSWORD = "X"

# ================= GROQ API CREDENTIALS =================
GROQ_API_KEY = "gsk_X"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 

# ================= COLOR MAPPING (RGB) =================
COLOR_MAP = {
    "שחור": (0, 0, 0), "לבן": (255, 255, 255), "אפור": (128, 128, 128),
    "כסף": (192, 192, 192), "אדום": (200, 0, 0), "ורוד": (255, 182, 193),
    "זהב": (212, 175, 55), "חום": (139, 69, 19), "טורקיז": (64, 224, 208),
    "ירוק": (0, 128, 0), "כחול": (0, 0, 200), "כתום": (255, 165, 0),
    "סגול": (128, 0, 128), "צהוב": (255, 215, 0)
}

FIXED_TAGS = ["תמונות לאורך"]

# ================= SWATCH DATA (EXISTING) =================
GLASS_SWATCH_DATA = {
    "מידות": {"swatch_type": "button"},
    "התקנה": {"swatch_type": "button"},
    "ספייסרים": {
        "swatch_type": "image",
        "values": {
            "זהב": {"image": {"url": "https://X.webp", "attachment_id": 14960}},
            "שחור": {"image": {"url": "https://X.webp", "attachment_id": 14961}},
            "כסוף": {"image": {"url": "https://X.webp", "attachment_id": 14962}}
        }
    }
}

FRAMED_SWATCH_DATA = {
    "מידות": {"swatch_type": "button"},
    "סוג מסגרת": {"swatch_type": "button"},
    "שוליים לבנים": {
        "swatch_type": "image",
        "values": {
            "בלי": {"image": {"url": "https://X.png", "attachment_id": 17612}},
            "עם": {"image": {"url": "https://X.png", "attachment_id": 17611}}
        }
    }
}

CANVAS_SWATCH_DATA = {
    "סוג": {"swatch_type": "button"},
    "מידות": {"swatch_type": "button"}
}

# ================= SWATCH DATA (NEW 3/2 PIECE) =================
SWATCH_DATA_3_PIECE_CANVAS = {} 

SWATCH_DATA_3_PIECE_FRAMED = {
    "מידות": {"swatch_type": "button"},
    "סוג מסגרת": {"swatch_type": "button"},
    "שוליים לבנים": {
        "swatch_type": "image",
        "values": {
            "בלי": {"image": {"url": "https://X.png", "attachment_id": 17612}},
            "עם": {"image": {"url": "https://X.png", "attachment_id": 17611}}
        }
    }
}

SWATCH_DATA_2_PIECE_CANVAS = {} 

SWATCH_DATA_2_PIECE_FRAMED = {
    "מידות": {"swatch_type": "button"},
    "סוג מסגרת": {"swatch_type": "button"},
    "שוליים לבנים": {
        "swatch_type": "image",
        "values": {
            "בלי": {"image": {"url": "https://X.png", "attachment_id": 17612}},
            "עם": {"image": {"url": "https://X.png", "attachment_id": 17611}}
        }
    }
}

# ================= CONFIGURATION =================
ALL_CATEGORIES = [
    "2 חלקים", "3 חלקים", "KAWS", "אבסטרקט", "אנימה", "אפריקאי", "בוהו",
    "גיימינג", "וינטג׳", "חיות", "כללי", "ליין ארט", "מוטיבציה", "מותגים",
    "מכוניות", "ספורט", "סרטים וסדרות", "פופ ארט", "שחור וזהב"
]

TYPE_TO_CATEGORY_MAP = {
    "Vertical Canvas": "תמונות קנבס",
    "Vertical Framed": "תמונות פוסטר עם מסגרת",
    "Vertical Glass": "תמונות זכוכית",
    "3 Piece Canvas": "3 חלקים",
    "3 Piece Framed": "3 חלקים",
    "2 Piece Canvas": "2 חלקים",
    "2 Piece Framed": "2 חלקים"
}

FILES_CONFIG = {
    # --- EXISTING ---
    "Vertical Canvas": {
        "prefix": "תמונת קנבס",
        "main_file": "תמונת לאורך.webp",
        "gallery_files": ["מוקאפ חדר קנבס.webp", "תלת מימד.webp", "רול פוסטר.webp"],
        "var_map": {"רול פוסטר": "רול פוסטר.webp", "רול קנבס": "רול פוסטר.webp", "פנימית": None}
    },
    "Vertical Framed": {
        "prefix": "תמונה עם מסגרת", # TIKUN 1: Changed from "תמונה ממוסגרת"
        "main_file": "תמונה עם מסגרת שחור.webp",
        "gallery_files": ["מוקאפ חדר תמונה עם מסגרת.webp", "תמונה עם מסגרת לבן.webp", "תמונה עם מסגרת עץ טבעי.webp", "רול פוסטר.webp"],
        "var_map": {"שחור": "תמונה עם מסגרת שחור.webp", "לבן": "תמונה עם מסגרת לבן.webp", "עץ": "תמונה עם מסגרת עץ טבעי.webp", "פוסטר": "רול פוסטר.webp"}
    },
    "Vertical Glass": {
        "prefix": "תמונת זכוכית",
        "main_file": "מוקאפ זכוכית.webp",
        "gallery_files": ["מוקאפ חדר זכוכית.webp"],
        "var_map": {"זכוכית": "מוקאפ זכוכית.webp"}
    },
    
    # --- NEW: 3 PIECE (Single File Logic) ---
    "3 Piece Canvas": {
        "prefix_fmt": "תמונות קנבס - {cat} - סט 3 חלקים",
        "main_file": "מוקאפ חדר קנבס 3 חלקים.webp",
        "gallery_files": [], 
        "var_map": {} 
    },
    "3 Piece Framed": {
        "prefix_fmt": "תמונות עם מסגרת - {cat} - סט 3 חלקים",
        "main_file": "מוקאפ חדר מסגרת 3 חלקים.webp",
        "gallery_files": [],
        "var_map": {}
    },

    # --- NEW: 2 PIECE (Single File Logic) ---
    "2 Piece Canvas": {
        "prefix_fmt": "תמונות קנבס - {cat} - סט 2 חלקים",
        "main_file": "מוקאפ חדר קנבס 2 חלקים.webp",
        "gallery_files": [],
        "var_map": {} 
    },
    "2 Piece Framed": {
        "prefix_fmt": "תמונות עם מסגרת - {cat} - סט 2 חלקים",
        "main_file": "מוקאפ חדר מסגרת 2 חלקים.webp",
        "gallery_files": [],
        "var_map": {}
    }
}

# ================= PRICING =================
CANVAS_PRICES = {
    ('רול קנבס בלבד', '100X150 ס"מ'): {'reg': '450', 'sale': '399'},
    ('רול קנבס בלבד', '70X100 ס"מ'): {'reg': '250', 'sale': '219'},
    ('רול קנבס בלבד', '50X70 ס"מ'): {'reg': '180', 'sale': '129'},
    ('רול קנבס בלבד', '40X50 ס"מ'): {'reg': '130', 'sale': '89'},
    ('קנבס עם מסגרת עץ (פנימית)', '40X50 ס"מ'): {'reg': '200', 'sale': '149'},
    ('קנבס עם מסגרת עץ (פנימית)', '50X70 ס"מ'): {'reg': '250', 'sale': '199'},
    ('קנבס עם מסגרת עץ (פנימית)', '70X100 ס"מ'): {'reg': '400', 'sale': '329'},
    ('קנבס עם מסגרת עץ (פנימית)', '100X150 ס"מ'): {'reg': '750', 'sale': '649'},
}

FRAMED_PRICES = {
    ('30X40', 'פוסטר בלבד'): {'reg': '80', 'sale': '59'},
    ('50X70', 'פוסטר בלבד'): {'reg': '200', 'sale': '149'},
    ('60X90', 'פוסטר בלבד'): {'reg': '300', 'sale': '249'},
    ('30X40', 'עץ מלא בצבע שחור'): {'reg': '200', 'sale': '149'},
    ('50X70', 'עץ מלא בצבע שחור'): {'reg': '400', 'sale': '299'},
    ('60X90', 'עץ מלא בצבע שחור'): {'reg': '550', 'sale': '459'},
    ('30X40', 'עץ מלא בצבע לבן'): {'reg': '200', 'sale': '149'},
    ('50X70', 'עץ מלא בצבע לבן'): {'reg': '400', 'sale': '299'},
    ('60X90', 'עץ מלא בצבע לבן'): {'reg': '550', 'sale': '459'},
    ('30X40', 'עץ מלא בצבע עץ'): {'reg': '200', 'sale': '149'},
    ('50X70', 'עץ מלא בצבע עץ'): {'reg': '400', 'sale': '299'},
    ('60X90', 'עץ מלא בצבע עץ'): {'reg': '550', 'sale': '459'},
}

GLASS_PRICES = {
    '70X100 ס״מ': {'reg': '1000', 'sale': '899'},
    '60X90 ס״מ': {'reg': '800', 'sale': '699'},
    '50X70 ס״מ': {'reg': '600', 'sale': '499'},
    '40X60 ס״מ': {'reg': '500', 'sale': '399'},
}

CANVAS_3_PIECE_PRICES = {
    ('קנבס + מסגרת עץ (פנימית)', '40X50 ס"מ'): {'reg': '450.0', 'sale': '399.0'},
    ('קנבס + מסגרת עץ (פנימית)', '50X70 ס"מ'): {'reg': '599.0', 'sale': '549.0'},
    ('קנבס + מסגרת עץ (פנימית)', '70X100 ס"מ'): {'reg': '920.0', 'sale': '859.0'},
    ('קנבס + מסגרת עץ (פנימית)', '100X150 ס"מ'): {'reg': '1900.0', 'sale': '1749.0'},
}

FRAMED_3_PIECE_PRICES = {
    ('30X40 ס"מ',): {'reg': '450.0', 'sale': '399.0'},
    ('50X70 ס"מ',): {'reg': '920.0', 'sale': '829.0'},
    ('61X91 ס"מ',): {'reg': '1299.0', 'sale': '1199.0'},
}

CANVAS_2_PIECE_PRICES = {
    ('100X150 ס"מ',): {'reg': '1300.0', 'sale': '1199.0'},
    ('70X100 ס"מ',): {'reg': '660.0', 'sale': '599.0'},
    ('50X70 ס"מ',): {'reg': '400.0', 'sale': '359.0'},
    ('40X50 ס"מ',): {'reg': '300.0', 'sale': '269.0'},
}

FRAMED_2_PIECE_PRICES = {
    ('60X90',): {'reg': '900.0', 'sale': '829.0'},
    ('50X70',): {'reg': '600.0', 'sale': '559.0'},
    ('30X40',): {'reg': '300.0', 'sale': '269.0'},
}

FRAME_COLORS_OPT = ["עץ מלא בצבע שחור", "עץ מלא בצבע לבן", "עץ מלא בצבע עץ"]
DESC_HTML = """<p>מחפשים ליצור אווירה יוקרתית ואישית בכל קיר? אצלנו בארטרי גלרי תמצאו אמנות שמשלבת אסתטיקה גבוהה עם איכות חומרים מובחרת.</p>"""

class UploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Uploader (Groq AI)")
        self.root.geometry("650x850")
        self.site_categories_map = {} 

        tk.Label(root, text="WooCommerce Auto-Uploader (Groq)", font=("Arial", 16, "bold"), fg="#006400").pack(pady=10)

        # 1. Product Type
        frame_top = tk.LabelFrame(root, text="1. Product Type", font=("Arial", 10, "bold"), padx=10, pady=5)
        frame_top.pack(fill="x", padx=20, pady=5)
        self.type_var = tk.StringVar(value="Vertical Canvas")
        self.type_menu = ttk.Combobox(frame_top, textvariable=self.type_var, state="readonly", width=40)
        self.type_menu['values'] = (
            "Vertical Canvas", "Vertical Framed", "Vertical Glass", 
            "3 Piece Canvas", "3 Piece Framed",
            "2 Piece Canvas", "2 Piece Framed",
            "ALL (Upload 3 Products)"
        )
        self.type_menu.pack()
        self.type_menu.bind("<<ComboboxSelected>>", self.update_preview)

        # 2. Categories
        frame_cat = tk.LabelFrame(root, text="2. Select Categories", font=("Arial", 10, "bold"), padx=10, pady=5)
        frame_cat.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_cat, text="Primary Category (SEO):").pack(anchor="w")
        self.cat1_var = tk.StringVar(value="אנימה")
        self.cat1_menu = ttk.Combobox(frame_cat, textvariable=self.cat1_var, state="readonly", width=40)
        self.cat1_menu['values'] = ALL_CATEGORIES
        self.cat1_menu.pack(pady=(0, 5))
        
        tk.Label(frame_cat, text="Secondary:").pack(anchor="w")
        self.cat2_var = tk.StringVar(value="None")
        self.cat2_menu = ttk.Combobox(frame_cat, textvariable=self.cat2_var, state="readonly", width=40)
        self.cat2_menu['values'] = ["None"] + ALL_CATEGORIES
        self.cat2_menu.pack(pady=(0, 5))

        tk.Label(frame_cat, text="Tertiary:").pack(anchor="w")
        self.cat3_var = tk.StringVar(value="None")
        self.cat3_menu = ttk.Combobox(frame_cat, textvariable=self.cat3_var, state="readonly", width=40)
        self.cat3_menu['values'] = ["None"] + ALL_CATEGORIES
        self.cat3_menu.pack()
        self.cat1_menu.bind("<<ComboboxSelected>>", self.update_preview)

        # 3. Settings
        frame_settings = tk.LabelFrame(root, text="3. Settings", font=("Arial", 10, "bold"), padx=10, pady=5)
        frame_settings.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_settings, text="Start Model ID:").grid(row=0, column=0, sticky="e")
        self.entry_start_id = tk.Entry(frame_settings, width=15)
        self.entry_start_id.insert(0, "10000")
        self.entry_start_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- AI KEYWORDS CHECKBOX ---
        self.var_ai_keywords = tk.BooleanVar(value=False)
        self.chk_ai = tk.Checkbutton(frame_settings, text="Enable Auto-Keywords (Groq AI)", variable=self.var_ai_keywords, fg="blue", font=("Arial", 10, "bold"))
        self.chk_ai.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w") # New Row for visibility
        # ----------------------------

        tk.Label(frame_settings, text="Name Preview:", fg="gray").grid(row=2, column=0, sticky="e")
        self.lbl_preview = tk.Label(frame_settings, text="...", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_preview.grid(row=2, column=1, sticky="w")
        self.update_preview()

        # 4. Folder
        self.folder_path = tk.StringVar()
        btn_folder = tk.Button(root, text="Select Master Folder", command=self.select_folder, bg="#e1e1e1", height=2)
        btn_folder.pack(fill="x", padx=40, pady=15)
        self.lbl_folder = tk.Label(root, text="No folder selected", fg="gray")
        self.lbl_folder.pack()

        # Check Lib
        if not PIL_AVAILABLE:
            tk.Label(root, text="Warning: Pillow (PIL) is required for Vision features.", fg="red").pack()

        # Run
        btn_run = tk.Button(root, text="START BATCH UPLOAD", command=self.start_thread, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2)
        btn_run.pack(fill="x", padx=40, pady=10)

        self.log_area = scrolledtext.ScrolledText(root, height=12, state='disabled')
        self.log_area.pack(padx=10, pady=10, fill="both", expand=True)

    def update_preview(self, event=None):
        p_type = self.type_var.get()
        cat = self.cat1_var.get()
        current_id = self.entry_start_id.get()
        
        if p_type == "ALL (Upload 3 Products)":
            self.lbl_preview.config(text=f"[Will create 3 products per folder] ID {current_id}")
        else:
            config = FILES_CONFIG.get(p_type)
            if not config:
                self.lbl_preview.config(text="Unknown Type")
                return

            if "prefix_fmt" in config:
                final_name = config["prefix_fmt"].format(cat=cat) + f" - דגם {current_id}"
            else:
                prefix = config.get("prefix", "???")
                final_name = f"{prefix} {cat} דגם {current_id}"
            
            self.lbl_preview.config(text=final_name)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.lbl_folder.config(text=folder, fg="black")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_thread(self):
        threading.Thread(target=self.run_upload, daemon=True).start()

    def get_cat_id(self, name):
        if name in self.site_categories_map: return self.site_categories_map[name]
        return None

    def upload_file(self, filepath, wcapi, wp_auth):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as img_data:
            files = {'file': (filename, img_data, 'image/webp')}
            res = requests.post(f"{SITE_URL}/wp-json/wp/v2/media", files=files, auth=wp_auth)
        if res.status_code == 201: return res.json()['id']
        return None

    def sort_sizes(self, size_list):
        def get_width(s):
            match = re.search(r'(\d+)', s)
            return int(match.group()) if match else 0
        return sorted(size_list, key=get_width)

    # ================= GROQ VISION (COLORS) =================
    def extract_colors(self, folder_path, filename="תמונת לאורך.webp"):
        target_file = os.path.join(folder_path, filename)
        if not os.path.exists(target_file):
            return []
        
        if not PIL_AVAILABLE:
            self.log("      [!] Vision Error: Pillow (PIL) missing.")
            return []

        try:
            with Image.open(target_file) as img:
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                max_size = 1024
                if max(img.size) > max_size: img.thumbnail((max_size, max_size))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=70) 
                buffer.seek(0)
                encoded_string = base64.b64encode(buffer.read()).decode('utf-8')

            valid_colors = list(COLOR_MAP.keys())
            valid_colors_str = ", ".join(valid_colors)
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt_text = (f"Analyze colors. Select exactly 3 from: {valid_colors_str}. "
                           f"Return JSON list strings. No markdown.")

            payload = {
                "model": GROQ_MODEL, 
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]}
                ],
                "temperature": 0.1, "max_tokens": 100
            }

            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                content = content.replace("```json", "").replace("```", "").strip()
                try:
                    detected = json.loads(content)
                    return [c for c in detected if c in valid_colors][:3]
                except: return []
            else: return []
        except Exception as e:
            self.log(f"      [!] Vision Error: {e}")
            return []

    # ================= GROQ VISION (KEYWORDS) =================
    def extract_keywords(self, folder_path, filename="תמונת לאורך.webp"):
        target_file = os.path.join(folder_path, filename)
        if not os.path.exists(target_file): return ""
        if not PIL_AVAILABLE: return ""

        try:
            with Image.open(target_file) as img:
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                max_size = 1024
                if max(img.size) > max_size: img.thumbnail((max_size, max_size))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=70) 
                buffer.seek(0)
                encoded_string = base64.b64encode(buffer.read()).decode('utf-8')

            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            
            prompt_text = (
                "Identify the specific main subject of this image (Famous Person, Character, Animal, Car Model, or Brand). "
                "Return ONLY the name in Hebrew and English separated by a space. "
                "Example: 'כריסטיאנו רונלדו Cristiano Ronaldo'. "
                "Do not write sentences. Do not write 'The image shows'. Just the keywords."
            )

            payload = {
                "model": GROQ_MODEL, 
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]}
                ],
                "temperature": 0.1, "max_tokens": 100
            }

            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # clean up potential markdown or periods
                clean_content = content.replace(".", "").strip()
                return clean_content
            else: 
                self.log(f"      [!] Groq API Error: {response.status_code}")
                return ""
        except Exception as e:
            self.log(f"      [!] Keyword Vision Error: {e}")
            return ""

    # ================= SINGLE PRODUCT PROCESSOR =================
    def process_single_product(self, folder_path, mode, model_id, wcapi, wp_auth):
        config = FILES_CONFIG.get(mode)
        if not config: return False

        # Name Generation Logic
        if "prefix_fmt" in config:
            prod_name = config["prefix_fmt"].format(cat=self.cat1_var.get()) + f" - דגם {model_id}"
        else:
            prod_name = f"{config['prefix']} {self.cat1_var.get()} דגם {model_id}"
            
        self.log(f" -> Processing: {prod_name} ({mode})")

        # 1. VISION
        detected_colors = []
        vision_file = config.get("main_file")
        
        # A. Colors Analysis (Always runs if PIL available)
        if vision_file:
             detected_colors = self.extract_colors(folder_path, vision_file)
        if detected_colors: 
            self.log(f"      Color Tags: {detected_colors}")
        
        # B. Keywords Analysis (Only if checkbox is enabled)
        if self.var_ai_keywords.get() and vision_file:
            self.log("      Analyzing Keywords (Groq)...")
            ai_keywords = self.extract_keywords(folder_path, vision_file)
            if ai_keywords:
                self.log(f"      [+] AI Found: {ai_keywords}")
                prod_name += f" - {ai_keywords}"
            else:
                self.log("      [-] No keywords detected.")

        # 2. Upload Images
        uploaded_ids = {}
        gallery_ids = []

        def upload_if_exists(fname):
            p = os.path.join(folder_path, fname)
            if os.path.exists(p):
                self.log(f"      Uploading: {fname}")
                return self.upload_file(p, wcapi, wp_auth)
            return None

        # Main Image
        main_file_path = os.path.join(folder_path, config["main_file"])
        if not os.path.exists(main_file_path):
            self.log(f"      [!] MISSING Main Image: {config['main_file']}")
            return False 

        main_id = upload_if_exists(config["main_file"])
        if not main_id: return False
        uploaded_ids[config["main_file"]] = main_id

        for gfile in config["gallery_files"]:
            gid = upload_if_exists(gfile)
            if gid:
                gallery_ids.append(gid)
                uploaded_ids[gfile] = gid

        # 3. Attributes setup
        attributes_data = []
        
        # --- VERTICAL ---
        if mode == "Vertical Canvas":
            sorted_sizes = self.sort_sizes(list(set([k[1] for k in CANVAS_PRICES])))
            attributes_data = [
                {"name": "סוג", "visible": False, "variation": True, "options": list(set([k[0] for k in CANVAS_PRICES]))},
                {"name": "מידות", "visible": False, "variation": True, "options": sorted_sizes}
            ]
        elif mode == "Vertical Framed":
            sorted_sizes = self.sort_sizes(list(set([k[0] for k in FRAMED_PRICES])))
            attributes_data = [
                {"name": "מידות", "visible": False, "variation": True, "options": sorted_sizes},
                {"name": "סוג מסגרת", "visible": False, "variation": True, "options": list(set([k[1] for k in FRAMED_PRICES]))},
                {"name": "שוליים לבנים", "visible": False, "variation": True, "options": ["בלי", "עם"]} 
            ]
        elif mode == "Vertical Glass":
            sorted_sizes = self.sort_sizes(list(GLASS_PRICES.keys()))
            attributes_data = [
                {"name": "מידות", "visible": False, "variation": True, "options": sorted_sizes},
                {"name": "ספייסרים", "visible": False, "variation": True, "options": ["זהב", "שחור", "כסוף"]},
                {"name": "התקנה", "visible": False, "variation": True, "options": ["תאמו לי התקנה - עלות התקנה 500₪", "ללא התקנה - אתקין בעצמי (באחריות הלקוח)"]}
            ]
        
        # --- 3 PIECE / 2 PIECE (CANVAS) ---
        elif "Piece Canvas" in mode:
            prices_dict = CANVAS_3_PIECE_PRICES if "3" in mode else CANVAS_2_PIECE_PRICES
            swatch_source = SWATCH_DATA_3_PIECE_CANVAS if "3" in mode else SWATCH_DATA_2_PIECE_CANVAS
            sample_key = list(prices_dict.keys())[0]
            if len(sample_key) == 2:
                types = list(set([k[0] for k in prices_dict]))
                sizes = self.sort_sizes(list(set([k[1] for k in prices_dict])))
                attributes_data.append({"name": "סוג", "visible": False, "variation": True, "options": types})
                attributes_data.append({"name": "מידות", "visible": False, "variation": True, "options": sizes})
            elif len(sample_key) == 1:
                sizes = self.sort_sizes(list(set([k[0] for k in prices_dict])))
                attributes_data.append({"name": "מידות", "visible": False, "variation": True, "options": sizes})
            if swatch_source and "שוליים לבנים" in swatch_source:
                 attributes_data.append({"name": "שוליים לבנים", "visible": False, "variation": True, "options": ["בלי", "עם"]})

        # --- 3 PIECE / 2 PIECE (FRAMED) ---
        elif "Piece Framed" in mode:
            prices_dict = FRAMED_3_PIECE_PRICES if "3" in mode else FRAMED_2_PIECE_PRICES
            swatch_source = SWATCH_DATA_3_PIECE_FRAMED if "3" in mode else SWATCH_DATA_2_PIECE_FRAMED
            sample_key = list(prices_dict.keys())[0]
            if len(sample_key) == 2:
                 sizes = self.sort_sizes(list(set([k[0] for k in prices_dict])))
                 frames = list(set([k[1] for k in prices_dict]))
                 attributes_data.append({"name": "מידות", "visible": False, "variation": True, "options": sizes})
                 attributes_data.append({"name": "סוג מסגרת", "visible": False, "variation": True, "options": frames})
            elif len(sample_key) == 1:
                 sizes = self.sort_sizes(list(set([k[0] for k in prices_dict])))
                 attributes_data.append({"name": "מידות", "visible": False, "variation": True, "options": sizes})
                 attributes_data.append({"name": "סוג מסגרת", "visible": False, "variation": True, "options": FRAME_COLORS_OPT})
            if swatch_source and "שוליים לבנים" in swatch_source:
                attributes_data.append({"name": "שוליים לבנים", "visible": False, "variation": True, "options": ["בלי", "עם"]})

        # 4. Tags & Categories
        cat_ids = []
        primary_cat_id = self.get_cat_id(self.cat1_var.get())
        if primary_cat_id: cat_ids.append({"id": primary_cat_id})
        
        gen_id = self.get_cat_id("כללי")
        if gen_id: cat_ids.append({"id": gen_id})
        
        sys_id = self.get_cat_id(TYPE_TO_CATEGORY_MAP.get(mode))
        if sys_id: cat_ids.append({"id": sys_id})

        if "Piece Canvas" in mode:
             extra_id = self.get_cat_id("תמונות קנבס")
             if extra_id: cat_ids.append({"id": extra_id})
        elif "Piece Framed" in mode:
             extra_id = self.get_cat_id("תמונות פוסטר עם מסגרת")
             if extra_id: cat_ids.append({"id": extra_id})

        u2 = self.get_cat_id(self.cat2_var.get())
        if u2: cat_ids.append({"id": u2})
        u3 = self.get_cat_id(self.cat3_var.get())
        if u3: cat_ids.append({"id": u3})
        
        cat_ids = [dict(t) for t in {tuple(d.items()) for d in cat_ids}]

        # TIKUN 2: Force "תמונות לאורך" tag by name
        final_tags = [{"name": t} for t in FIXED_TAGS]
        
        if detected_colors:
            for color in detected_colors: final_tags.append({"name": color})

        # SEO Logic
        seo_kw = ""
        if "Canvas" in mode: seo_kw = "תמונות לבית קנבס"
        elif "Framed" in mode: seo_kw = "תמונה עם מסגרת"
        elif "Glass" in mode: seo_kw = "תמונת זכוכית"

        meta_data_list = [
            {"key": "_yoast_wpseo_focuskw", "value": seo_kw},
            {"key": "_yoast_wpseo_content_score", "value": "90"},
            {"key": "_wc_facebook_sync_enabled", "value": "yes"}
        ]
        if primary_cat_id:
            meta_data_list.append({"key": "_yoast_wpseo_primary_product_cat", "value": str(primary_cat_id)})
        
        swatch_dict = {}
        if mode == "Vertical Glass": swatch_dict = GLASS_SWATCH_DATA
        elif mode == "Vertical Framed": swatch_dict = FRAMED_SWATCH_DATA
        elif mode == "Vertical Canvas": swatch_dict = CANVAS_SWATCH_DATA
        elif mode == "3 Piece Canvas": swatch_dict = SWATCH_DATA_3_PIECE_CANVAS
        elif mode == "3 Piece Framed": swatch_dict = SWATCH_DATA_3_PIECE_FRAMED
        elif mode == "2 Piece Canvas": swatch_dict = SWATCH_DATA_2_PIECE_CANVAS
        elif mode == "2 Piece Framed": swatch_dict = SWATCH_DATA_2_PIECE_FRAMED

        if swatch_dict:
            swatch_json_str = json.dumps(swatch_dict, separators=(',', ':'), ensure_ascii=False)
            meta_data_list.append({"key": "_ct-woo-attributes-list", "value": swatch_json_str})

        # 5. Create Product
        product_data = {
            "name": prod_name,
            "type": "variable",
            "status": "publish",
            "description": DESC_HTML,
            "images": [{"id": main_id}] + [{"id": gid} for gid in gallery_ids],
            "categories": cat_ids,
            "tags": final_tags,
            "attributes": attributes_data,
            "meta_data": meta_data_list
        }

        try:
            prod_res = wcapi.post("products", product_data).json()
            if 'id' not in prod_res:
                self.log(f"      [!] Create Fail: {prod_res}")
                return False
            pid = prod_res['id']
            self.log(f"      [V] Product Created ID: {pid}")

            # 6. Variations
            if mode == "Vertical Canvas":
                for (p_type, p_size), prices in CANVAS_PRICES.items():
                    vid = main_id
                    for key, fname in config["var_map"].items():
                        if fname and key in p_type and fname in uploaded_ids: 
                            vid = uploaded_ids[fname]; break
                    wcapi.post(f"products/{pid}/variations", {
                        "regular_price": prices['reg'], "sale_price": prices['sale'],
                        "attributes": [{"name": "סוג", "option": p_type}, {"name": "מידות", "option": p_size}],
                        "image": {"id": vid}
                    })
            elif mode == "Vertical Framed":
                for (p_size, p_type), prices in FRAMED_PRICES.items():
                    vid = main_id
                    for key, fname in config["var_map"].items():
                        if fname and key in p_type and fname in uploaded_ids: 
                            vid = uploaded_ids[fname]; break
                    wcapi.post(f"products/{pid}/variations", {
                        "regular_price": prices['reg'], "sale_price": prices['sale'],
                        "attributes": [{"name": "מידות", "option": p_size}, {"name": "סוג מסגרת", "option": p_type}],
                        "image": {"id": vid}
                    })
            elif mode == "Vertical Glass":
                for p_size, prices in GLASS_PRICES.items():
                    wcapi.post(f"products/{pid}/variations", {
                        "regular_price": prices['reg'], "sale_price": prices['sale'],
                        "attributes": [{"name": "מידות", "option": p_size}],
                        "image": {"id": main_id}
                    })
            
            elif "Piece Canvas" in mode:
                prices_dict = CANVAS_3_PIECE_PRICES if "3" in mode else CANVAS_2_PIECE_PRICES
                for key_tuple, prices in prices_dict.items():
                    attr_list = []
                    if len(key_tuple) == 2:
                        attr_list.append({"name": "סוג", "option": key_tuple[0]})
                        attr_list.append({"name": "מידות", "option": key_tuple[1]})
                    elif len(key_tuple) == 1:
                        attr_list.append({"name": "מידות", "option": key_tuple[0]})
                    wcapi.post(f"products/{pid}/variations", {
                        "regular_price": prices['reg'], "sale_price": prices['sale'],
                        "attributes": attr_list,
                        "image": {"id": main_id}
                    })
            
            elif "Piece Framed" in mode:
                prices_dict = FRAMED_3_PIECE_PRICES if "3" in mode else FRAMED_2_PIECE_PRICES
                for key_tuple, prices in prices_dict.items():
                    attr_list = []
                    if len(key_tuple) == 2:
                        attr_list.append({"name": "מידות", "option": key_tuple[0]})
                        attr_list.append({"name": "סוג מסגרת", "option": key_tuple[1]})
                    elif len(key_tuple) == 1:
                         attr_list.append({"name": "מידות", "option": key_tuple[0]})
                    wcapi.post(f"products/{pid}/variations", {
                        "regular_price": prices['reg'], "sale_price": prices['sale'],
                        "attributes": attr_list,
                        "image": {"id": main_id}
                    })

            return True

        except Exception as e:
            self.log(f"      [!] Error: {e}")
            return False

    def run_upload(self):
        selected_mode = self.type_var.get()
        master_folder = self.folder_path.get()
        try: start_id = int(self.entry_start_id.get())
        except: self.log("Invalid Start ID"); return
        if not master_folder: self.log("No folder selected"); return

        self.log(f"--- Starting Batch (Groq): {selected_mode} ---")
        wcapi = API(url=SITE_URL, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, version="wc/v3", timeout=60)
        wp_auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD.replace(" ", ""))
        
        self.log("Loading Categories...")
        page=1
        while True:
            r = wcapi.get("products/categories", params={"per_page": 100, "page": page})
            if r.status_code!=200 or not r.json(): break
            for c in r.json():
                self.site_categories_map[c['name']] = c['id']
                self.site_categories_map[c['name'].replace('׳', "'")] = c['id']
            page+=1
        
        subfolders = [f.path for f in os.scandir(master_folder) if f.is_dir()]
        if not subfolders: subfolders = [master_folder]
        subfolders.sort()

        current_id = start_id
        for product_folder in subfolders:
            folder_name = os.path.basename(product_folder)
            self.log(f"\n[Folder] {folder_name} | Model ID: {current_id}")

            if selected_mode == "ALL (Upload 3 Products)":
                self.process_single_product(product_folder, "Vertical Canvas", current_id, wcapi, wp_auth)
                self.process_single_product(product_folder, "Vertical Framed", current_id, wcapi, wp_auth)
                self.process_single_product(product_folder, "Vertical Glass", current_id, wcapi, wp_auth)
            else:
                self.process_single_product(product_folder, selected_mode, current_id, wcapi, wp_auth)

            current_id += 1
            time.sleep(1) # Faster delay for Groq

        self.log("\n--- COMPLETE ---")
        messagebox.showinfo("Success", "Batch Upload Complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = UploaderApp(root)
    root.mainloop()
