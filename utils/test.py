import requests
from openai import OpenAI
import base64

import os
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "http://localhost:8520"
BYOC_AUTH = f"{os.getenv('Y2O_CatalogID', 'test')}:{os.getenv('Y2O_SecretKey', 'test')}"
TOKEN_AUTH = os.getenv('Y2O_TestToken', 'test')

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
PINK = '\033[95m'
RESET = '\033[0m'

class Y2Otest:
    def __init__(self, base_url="http://localhost:8520", byoc_auth=None, token_auth=None):
        self.base_url = base_url
        self.byoc_auth = byoc_auth
        self.token_auth = token_auth
        self.client = None
    
    def init_client(self, mode="byoc"):
        if mode == "byoc":
            print(f"{CYAN}Initializing client with {PINK}BYOC{CYAN} auth{RESET}")
            api_key = self.byoc_auth
        elif mode == "token":
            print(f"{CYAN}Initializing client with {PINK}token{CYAN} auth{RESET}")
            api_key = self.token_auth
        else:
            raise ValueError("Invalid mode. Must be 'byoc' or 'token'")
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

    def test_all(self):
        """Run all tests"""
        status = {
            "health": self.test_health(),
            "models": self.test_models(),
            "completions": self.test_completions(),
            "completions_streaming": self.test_completions_streaming(),
            "embeddings": self.test_embeddings(),
            "image_generation": self.test_image_generation(),
        }
        if all(status.values()):
            print(f"\n{GREEN}* All tests passed{RESET}")
        else:
            print(f"\n{RED}* Some tests failed{RESET}")
            for k, v in status.items():
                if not v:
                    print(f"  - {PINK}{k}{RESET}")
        print("\n")

    def test_health(self):
        """Test the health endpoint"""
        print(f"\n=== {YELLOW}Testing Health Endpoint{RESET} ===")
        url = f"{self.base_url}/health"
        response = requests.get(url)
        if response.status_code == 200:
            print(response.text)
            print(f"{GREEN}Health check passed{RESET}")
            return True
        else:
            print(response.text)
            print(f"{RED}Health check failed{RESET}")
            exit(1)

    def test_models(self):
        """Test the models endpoint"""
        print(f"\n=== {YELLOW}Testing Models{RESET} ===")
        try:
            models = self.client.models.list()
            print(f"Models count: {len(models.data)}")
            print(f"{GREEN}Good{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Failed to get models list:{RESET} {e}")
            return False
        
    def test_completions(self, model="yandexgpt/latest"):
        """Test the completions endpoint"""
        print(f"\n=== {YELLOW}Testing Completions{RESET} ===")
        print(f"Model: `{model}`")
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test",
                    }
                ],
                model=model
            )
            response_text = response.choices[0].message.content
            print(response_text)
            print(f"{GREEN}Good{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Failed to generate completion:{RESET} {e}")
            return False
        
    def test_completions_streaming(self, model="yandexgpt/latest"):
        """Test the completions endpoint"""
        print(f"\n=== {YELLOW}Testing Completions (Streaming){RESET} ===")
        print(f"Model: `{model}`")
        try:
            stream = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test",
                    }
                ],
                model=model,
                stream=True,
            )
            for chunk in stream:
                print(chunk.choices[0].delta.content or "", end="")
            print(f"\n{GREEN}Good{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Failed to generate completion:{RESET} {e}")
            return False
        
    def test_embeddings(self, model="text-search-query/latest"):
        """Test the embeddings endpoint"""
        print(f"\n=== {YELLOW}Testing Embeddings{RESET} ===")
        print(f"Model: `{model}`")
        try:
            # 1
            print("Text: \"Your text string goes here\"")
            response = self.client.embeddings.create(
                input="Your text string goes here",
                model=model
            )
            print(f"Length: {len(response.data[0].embedding)}")
            # 2
            print("Text: [\"Your text string goes here\"]")
            response = self.client.embeddings.create(
                input=["Your text string goes here"],
                model=model
            )
            print(f"Length: {len(response.data[0].embedding)}")
            # 3
            print("Text: [\"Your text string goes here\", \"Your text string goes here\"]")
            response = self.client.embeddings.create(
                input=["Your text string goes here", "Your text string goes here"],
                model=model
            )
            print(f"Length: {len(response.data[0].embedding)}, {len(response.data[1].embedding)}")
            print(f"{GREEN}Good{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Failed to generate embeddings:{RESET} {e}")
            # import traceback
            # traceback.print_exc()
            return False
        
    def test_image_generation(self, model="yandex-art/latest"):
        """Test the image generation endpoint"""
        print(f"\n=== {YELLOW}Testing Image Generation{RESET} ===")
        print(f"Model: `{model}`")
        try:
            response = self.client.images.generate(
                model=model,
                prompt="A black cat with green eyes, sitting on a wooden floor",
                size="1024x1024",
                response_format="b64_json"
            )
            b64_image = response.data[0].b64_json
            print(f"Image generated (b64 length: {len(b64_image)})")
            with open("test.jpg", "wb") as f:
                f.write(base64.b64decode(b64_image))
            print(f"{GREEN}Good{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Failed to generate image:{RESET} {e}")
            return False
        

if __name__ == "__main__":
    print(f"{YELLOW}=== Y2O Testing ==={RESET}")
    test = Y2Otest(base_url=BASE_URL, byoc_auth=BYOC_AUTH, token_auth=TOKEN_AUTH)
    try:
        input(f"Press {GREEN}Enter{RESET} to start testing or {RED}Ctrl+C{RESET} to pass ({PINK}BYOC{RESET})")
        test.init_client(mode="byoc")
        test.test_all()
    except KeyboardInterrupt:
        pass
    try:
        input(f"Press {GREEN}Enter{RESET} to start testing or {RED}Ctrl+C{RESET} to pass ({PINK}Token{RESET})")
        test.init_client(mode="token")
        test.test_all()
    except KeyboardInterrupt:
        pass
    input(f"Done. Press {GREEN}Enter{RESET} to exit")
    if os.path.exists("test.jpg"):
        os.remove("test.jpg")
