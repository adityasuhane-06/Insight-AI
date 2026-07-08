import uvicorn
from main import app

# Hugging Face Spaces with Gradio SDK will execute this app.py file.
# By explicitly binding our FastAPI app to 0.0.0.0:7860, we can trick
# the Gradio SDK into hosting our pure FastAPI backend for free!

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
