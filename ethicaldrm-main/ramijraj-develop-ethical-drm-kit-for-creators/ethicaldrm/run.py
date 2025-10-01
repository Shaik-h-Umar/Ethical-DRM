# run.py
from waitress import serve
# 1. Import the create_app function, not the 'app' object
from ethicaldrm.api.app import create_app
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
from waitress import serve

# --- THIS IS THE SMART CODE BLOCK YOU DELETED ---
# It finds the .env file that is in the same folder as this run.py script
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')

# Load the .env file from that specific path BEFORE the app starts
load_dotenv(dotenv_path)
# --- END OF BLOCK ---

# Now we can import the app, because the API key is already loaded
from ethicaldrm.api.app import create_app

    
if __name__ == "__main__":
    # Call the function to create the app instance
    app = create_app()

    print("Starting server with Waitress on http://127.0.0.1:5000")
    
    # 3. Serve the app instance we just created
    serve(app, host="127.0.0.1", port=5000)