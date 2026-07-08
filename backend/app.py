import gradio as gr
import spaces
from main import app as fastapi_app

@spaces.GPU
def health():
    return "Insight AI API is running on ZeroGPU!"

demo = gr.Interface(fn=health, inputs=[], outputs="text")

import uvicorn

# Mount the Gradio app to the FastAPI app at /gradio
# Hugging Face Spaces Gradio SDK expects 'app' to be an ASGI app or Gradio block
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
