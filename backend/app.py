import gradio as gr
from main import app as fastapi_app

def health():
    return "Insight AI API is running!"

demo = gr.Interface(fn=health, inputs=[], outputs="text")

# Mount the Gradio app to the FastAPI app at /gradio
# Hugging Face Spaces Gradio SDK expects 'app' to be an ASGI app or Gradio block
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
