AI-Powered E-Commerce Automation Suite

Automated Mockup Generation & Smart Product Injection

📖 Overview

This repository contains a two-part automation suite designed to handle the entire lifecycle of a digital art product—from a flat design to a live, SEO-optimized WooCommerce product.

Mockup Engine (CombinedBot.py): A Python-based desktop application that automates Adobe Photoshop via COM integration to place designs into high-quality PSD templates. It simultaneously uses Google Gemini 2.0 Flash to generate photorealistic AI room mockups based on the artwork's vibe.

Product Uploader (WooCommerceUploader.py): A batch processing tool that uses Groq (Llama Vision) to "see" the generated images, extract dominant colors, and suggest SEO keywords. It then creates complex variable products (Canvas, Framed, Glass) on WooCommerce with pre-configured pricing and attributes.

🚀 Key Features

Engine 1: Visual Automation
Photoshop Scripting: Automates Smart Object replacement and WebP export for high-performance web images.

AI Room Generation: Integrates Gemini AI to create diverse interior mockups (Canvas, Frame, Glass) that match the style of the design.

Batch Processing: Handles single images or entire folders of designs automatically.

Engine 2: Smart Distribution
Computer Vision (Llama Vision): Automatically detects product colors and identifies subjects to generate dynamic product titles and tags.

Complex Variation Logic: Handles multi-attribute pricing (Size vs. Frame Type vs. Material) in a single upload cycle.

SEO Optimization: Automatically injects Focus Keywords and Content Scores for Yoast SEO integration.

🛠️ Tech Stack

Language: Python (Tkinter for GUI).

AI Integration: Google Gemini API & Groq Cloud API.

Design Automation: Adobe Photoshop COM Object (win32com).

E-commerce: WooCommerce REST API.

Image Processing: Pillow (PIL).

⚙️ Installation
Requirements: Python 3.10+, Adobe Photoshop (for the Mockup Engine), and a WooCommerce store.

API Keys: Obtain keys for Gemini, Groq, and WooCommerce REST API.

Setup: Replace the placeholders in the CONFIG section of each script with your credentials.

<img width="525" height="659" alt="PhotoshopBot" src="https://github.com/user-attachments/assets/e4d49dc5-ebf4-4816-98dc-824f7eb800a7" />


<img width="487" height="661" alt="WooCommerceUploader" src="https://github.com/user-attachments/assets/d136ae8f-c1b6-4855-8e61-a9a698e9c69f" />

