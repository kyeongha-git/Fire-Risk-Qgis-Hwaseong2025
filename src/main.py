import argparse
import os
import subprocess
import sys
from pyngrok import ngrok, conf

def run():
    parser = argparse.ArgumentParser(description="Fire Risk Map Dashboard Launcher")
    
    parser.add_argument(
        "--openai_key", 
        type=str, 
        required=True, 
        help="OpenAI API Key (sk-...)"
    )
    
    parser.add_argument(
        "--ngrok_key", 
        type=str, 
        required=False, 
        help="Ngrok Authtoken (Optional if already configured)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8502,
        help="Port to run Streamlit on"
    )

    args = parser.parse_args()

    # 2. Set OpenAI API key as environment variable for app.py to access
    os.environ["OPENAI_API_KEY"] = args.openai_key

    # 3. Set Ngrok auth token if provided
    if args.ngrok_key:
        conf.get_default().auth_token = args.ngrok_key

    # 4. Start Ngrok tunnel
    try:
        public_url = ngrok.connect(args.port).public_url
        print(f"\n========================================================")
        print(f"Public URL: {public_url}")
        print(f"========================================================\n")
    except Exception as e:
        print(f"Ngrok connection failed: {e}")
        print("Running locally only.")

    # 5. Start Streamlit app (app.py)
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    cmd = [
        "streamlit", "run", app_path,
        f"--server.port={args.port}",
        "--server.headless=true"
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        ngrok.kill()

if __name__ == "__main__":
    run()