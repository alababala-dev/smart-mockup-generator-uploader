import os
import sys
import time
import ctypes
import io
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import win32com.client
from PIL import Image

# --- GOOGLE GENAI IMPORTS ---
try:
    from google import genai
    from google.genai import types
except ImportError:
    messagebox.showerror("Error", "Google GenAI library not found.\nPlease run: pip install google-genai")
    sys.exit()

# --- CONFIGURATION (CLEANSED) ---
# Replace this with your actual API Key or use an environment variable
API_KEY = "YOUR_GEMINI_API_KEY_HERE" 
MODEL_NAME = "gemini-2.0-flash"

# --- AUTO-ADMINISTRATOR ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Ensure script runs with admin privileges to interact with Photoshop COM
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

class CombinedMockupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Commerce Mockup Automator (Photoshop + AI)")
        self.root.geometry("700x850")

        # --- Variables ---
        self.mockup_base_folder = tk.StringVar()
        self.selected_category = tk.StringVar()
        self.input_path = tk.StringVar()
        self.is_batch = tk.BooleanVar()
        self.generation_mode = tk.StringVar(value="All") # Options: Canvas, Frame, Glass, All
        self.status_var = tk.StringVar(value="Ready.")
        
        self.config_file = "bot_settings.txt"
        
        # --- AI Client Setup ---
        self.ai_client = None
        self.setup_ai_client()

        self.create_widgets()
        self.load_settings()

    def setup_ai_client(self):
        try:
            self.ai_client = genai.Client(
                api_key=API_KEY,
                http_options=types.HttpOptions(timeout=300000) # 5-minute timeout for image gen
            )
        except Exception as e:
            messagebox.showwarning("AI Warning", f"Could not initialize AI Client: {e}")

    def create_widgets(self):
        # Header
        tk.Label(self.root, text="Mockup Generation Suite", font=("Arial", 18, "bold")).pack(pady=10)

        # 1. Photoshop Library
        frame1 = tk.LabelFrame(self.root, text="1. Photoshop Library (Existing PSDs)", padx=10, pady=5)
        frame1.pack(fill="x", padx=20)
        tk.Button(frame1, text="Select Main PSD Folder", command=self.select_mockup_folder).pack(anchor="w")
        tk.Label(frame1, textvariable=self.mockup_base_folder, fg="gray", wraplength=600).pack(anchor="w")
        
        tk.Label(frame1, text="Select Category Subfolder:").pack(anchor="w", pady=(5,0))
        self.cat_menu = ttk.Combobox(frame1, textvariable=self.selected_category, state="readonly", width=50)
        self.cat_menu.pack(anchor="w", pady=5)

        # 2. Input
        frame2 = tk.LabelFrame(self.root, text="2. Input Designs (Jpg/Png)", padx=10, pady=5)
        frame2.pack(fill="x", padx=20, pady=10)
        tk.Button(frame2, text="Select Single Image", command=lambda: self.select_input("single")).pack(side=tk.LEFT, padx=5)
        tk.Button(frame2, text="Select Folder (Batch)", command=lambda: self.select_input("batch")).pack(side=tk.LEFT, padx=5)
        tk.Label(self.root, textvariable=self.input_path, fg="blue", wraplength=500).pack(pady=5)

        # 3. Mode Selection
        frame3 = tk.LabelFrame(self.root, text="3. Generation Mode", padx=10, pady=5)
        frame3.pack(fill="x", padx=20)
        
        modes = [("Generate ALL", "All"), 
                 ("Canvas Only", "Canvas"), 
                 ("Frame Only", "Frame"), 
                 ("Glass Only", "Glass")]
        
        for text, mode in modes:
            tk.Radiobutton(frame3, text=text, variable=self.generation_mode, value=mode, font=("Arial", 10)).pack(anchor="w")

        # 4. Log Area
        tk.Label(self.root, text="Activity Log:").pack(anchor="w", padx=20, pady=(10,0))
        self.log_text = scrolledtext.ScrolledText(self.root, height=12, state='disabled', font=("Consolas", 9))
        self.log_text.pack(fill="both", padx=20, pady=5, expand=True)

        # 5. Run Button
        tk.Button(self.root, text="START PROCESSING", bg="#28a745", fg="white", font=("Arial", 14, "bold"), 
                  command=self.start_processing_thread).pack(pady=10, ipadx=30, ipady=5)

        tk.Label(self.root, textvariable=self.status_var, fg="red", font=("Arial", 10, "bold")).pack(side=tk.BOTTOM, pady=10)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def save_settings(self):
        try:
            with open(self.config_file, "w") as f:
                f.write(self.mockup_base_folder.get())
        except: pass

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    saved_path = f.read().strip()
                if os.path.exists(saved_path):
                    self.mockup_base_folder.set(saved_path)
                    self.refresh_categories(saved_path)
            except: pass

    def select_mockup_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.mockup_base_folder.set(f)
            self.save_settings()
            self.refresh_categories(f)

    def refresh_categories(self, folder_path):
        try:
            subs = [d.name for d in os.scandir(folder_path) if d.is_dir()]
            self.cat_menu['values'] = subs
            if subs: self.cat_menu.current(0)
        except: pass

    def select_input(self, mode):
        if mode == "single":
            f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
            self.is_batch.set(False)
        else:
            f = filedialog.askdirectory()
            self.is_batch.set(True)
        if f: self.input_path.set(f)

    def start_processing_thread(self):
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        if not self.mockup_base_folder.get() or not self.selected_category.get() or not self.input_path.get():
            messagebox.showerror("Error", "Please select Library, Category, and Input Design(s).")
            return

        self.status_var.set("Initializing Photoshop...")
        self.log("--- Starting New Batch ---")

        # 1. Connect to Photoshop via COM
        try:
            psApp = win32com.client.Dispatch("Photoshop.Application")
            psApp.Visible = True
            psApp.DisplayDialogs = 3  # Disable dialogs for silent operation
            psApp.Preferences.RulerUnits = 1 # Pixels
        except Exception as e:
            self.log(f"CRITICAL: Photoshop connection failed. {e}")
            messagebox.showerror("Error", f"Photoshop Error: {e}")
            return

        # 2. Gather PSD templates
        cat_path = os.path.join(self.mockup_base_folder.get(), self.selected_category.get())
        psd_files = []
        for root_dir, dirs, files in os.walk(cat_path):
            for file in files:
                if file.lower().strip().endswith((".psd", ".psb")) and not file.startswith("~"):
                    psd_files.append(os.path.join(root_dir, file))
        
        self.log(f"Found {len(psd_files)} PSD templates in library.")

        # 3. Gather Designs to process
        design_files = []
        if self.is_batch.get():
            fol = self.input_path.get()
            design_files = [os.path.join(fol, x) for x in os.listdir(fol) if x.lower().endswith(('.jpg','.png','.jpeg'))]
        else:
            design_files = [self.input_path.get()]
        
        self.log(f"Found {len(design_files)} Design images to process.")

        # 4. Main Loop
        total = len(design_files)
        for i, design_path in enumerate(design_files):
            d_name = os.path.splitext(os.path.basename(design_path))[0]
            self.status_var.set(f"Processing {i+1}/{total}: {d_name}")
            self.log(f"\nProcessing Design: {d_name}")

            # Define Output Folder
            base_out_dir = os.path.join(os.path.dirname(design_path), f"{d_name}_Mockups")
            if not os.path.exists(base_out_dir): os.makedirs(base_out_dir)

            mode = self.generation_mode.get()
            
            # --- PART A: PHOTOSHOP AUTOMATION ---
            self.log(f"  > Executing Photoshop scripts for {len(psd_files)} templates...")
            for psd in psd_files:
                try:
                    self.process_photoshop_file(psApp, psd, design_path, base_out_dir)
                except Exception as e:
                    self.log(f"    - PS Error on {os.path.basename(psd)}: {e}")

            # --- PART B: GENAI IMAGE GENERATION ---
            self.log(f"  > Initiating AI Generation (Mode: {mode})...")
            
            try:
                img_obj = Image.open(design_path)
                
                if mode == "Canvas" or mode == "All":
                    self.generate_ai_image(
                        "Photorealistic interior mockup. Place this EXACT artwork as a frameless Gallery Wrap Canvas on a wall.",
                        img_obj, "Canvas", base_out_dir
                    )

                if mode == "Frame" or mode == "All":
                    self.generate_ai_image(
                        "Photorealistic interior mockup. Place this EXACT artwork inside a stylish wooden picture frame.",
                        img_obj, "Frame", base_out_dir
                    )

                if mode == "Glass" or mode == "All":
                    self.generate_ai_image(
                        "Photorealistic interior mockup. Place this EXACT artwork as a modern Acrylic Glass Print with metal standoffs.",
                        img_obj, "Glass", base_out_dir
                    )
            except Exception as e:
                self.log(f"  > AI Setup Error: {e}")

        self.status_var.set("All Done.")
        self.log("\n--- BATCH COMPLETE ---")
        messagebox.showinfo("Success", "Batch processing finished!")

    def process_photoshop_file(self, psApp, psd_path, design_path, out_dir):
        doc = psApp.Open(psd_path)
        
        def find_so(layers):
            """Recursively find a Smart Object Kind layer."""
            for lay in layers:
                try:
                    if lay.Kind == 17: return lay # 17 = Smart Object
                except: pass
                try:
                    if lay.TypeName == "LayerSet":
                        found = find_so(lay.ArtLayers)
                        if not found: found = find_so(lay.LayerSets)
                        if found: return found
                except: pass
            return None

        try:
            so = find_so(doc.Layers)
            if not so: raise Exception("Target Smart Object not found.")

            psApp.ActiveDocument = doc
            doc.ActiveLayer = so
            
            # Open Smart Object Content
            psApp.ExecuteAction(psApp.StringIDToTypeID("placedLayerEditContents"), win32com.client.Dispatch("Photoshop.ActionDescriptor"), 3)
            smart_doc = psApp.ActiveDocument
            
            target_w = smart_doc.Width
            target_h = smart_doc.Height
            
            # Place New Design
            idPlc = psApp.CharIDToTypeID("Plc ")
            desc = win32com.client.Dispatch("Photoshop.ActionDescriptor")
            desc.PutPath(psApp.CharIDToTypeID("null"), design_path)
            psApp.ExecuteAction(idPlc, desc, 3)
            
            placed_layer = smart_doc.ActiveLayer
            bounds = placed_layer.Bounds
            w = bounds[2] - bounds[0]
            h = bounds[3] - bounds[1]
            
            # Proportional Resize
            if w > 0 and h > 0:
                scale_x = (target_w / w) * 100
                scale_y = (target_h / h) * 100
                placed_layer.Resize(scale_x, scale_y)
                
            smart_doc.Close(1) # Save & Close Smart Object doc
            
            clean_psd_name = os.path.splitext(os.path.basename(psd_path))[0]
            webp_path = os.path.join(out_dir, f"{clean_psd_name}.webp")

            # Save as WebP
            desc = win32com.client.Dispatch("Photoshop.ActionDescriptor")
            webP_options = win32com.client.Dispatch("Photoshop.ActionDescriptor")
            webP_options.PutInteger(psApp.StringIDToTypeID("compressionType"), 0) 
            webP_options.PutInteger(psApp.StringIDToTypeID("quality"), 75) 
            
            desc.PutObject(psApp.CharIDToTypeID("As  "), psApp.StringIDToTypeID("WebPFormat"), webP_options)
            desc.PutPath(psApp.CharIDToTypeID("In  "), webp_path)
            desc.PutBoolean(psApp.CharIDToTypeID("Cpy "), True) 
            psApp.ExecuteAction(psApp.CharIDToTypeID("save"), desc, 3)
            
        finally:
            doc.Close(2) # Close parent PSD without saving

    def generate_ai_image(self, prompt, image_file, type_label, output_folder):
        if not self.ai_client:
            self.log(f"    - AI skipped: {type_label}")
            return

        full_prompt = (
            f"{prompt} Setting: A modern, high-end residential interior. "
            "The decor should complement the artwork's color palette. "
            "Ensure the artwork is centered and occupies a significant portion of the image."
        )

        # Standardized file labels for downstream automation
        labels = {
            "Canvas": "mockup-room-canvas",
            "Frame": "mockup-room-framed",
            "Glass": "mockup-room-glass"
        }
        
        filename = f"{labels.get(type_label, type_label)}.webp"
        attempt = 0
        max_attempts = 5 

        while attempt < max_attempts:
            attempt += 1
            try:
                response = self.ai_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[full_prompt, image_file],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="1:1")
                    )
                )
                
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        save_path = os.path.join(output_folder, filename)
                        img = Image.open(io.BytesIO(part.inline_data.data))
                        img.save(save_path, "WEBP", quality=95)
                        self.log(f"    - [AI SUCCESS] Generated {filename}")
                        return

                self.log(f"    - [AI Retry] {type_label}: Image missing in response.")
            
            except Exception as e:
                error_str = str(e)
                if any(x in error_str for x in ["503", "429", "504", "Deadline"]):
                    time.sleep(attempt * 5)
                else:
                    self.log(f"    - [AI ERROR] {type_label}: {e}")
                    return

        self.log(f"    - [AI FAILED] {type_label} after {max_attempts} attempts.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CombinedMockupApp(root)
    root.mainloop()