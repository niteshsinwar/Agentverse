# =========================================
# File: run_gradio.py
# Purpose: Entrypoint (kept minimal); import APP from app/ui/gradio_app.py
# =========================================
import os
from dotenv import load_dotenv
import gradio as gr

# Load environment variables from .env file
load_dotenv()

from app.ui.gradio_app import APP

if __name__ == "__main__":
    APP.queue().launch(server_name="0.0.0.0", server_port=7860, share=False)