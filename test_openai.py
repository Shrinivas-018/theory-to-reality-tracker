import os
import sys

# Set the api key for testing
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.yuga_generator import YugaGeneratorService

def test_generation():
    generator = YugaGeneratorService()
    print("Testing OpenAI API through YugaGeneratorService...")
    print(f"Using model: {generator.model}")
    print(f"API URL: {generator.api_url}")
    
    # Try generating a small evolution
    result = generator.generate_yuga_evolution("Computer", "A device that computes.", rich_content=False)
    if result:
        print("Success! Got a response:")
        print(list(result.keys()))
    else:
        print("Failed to get response.")

if __name__ == "__main__":
    test_generation()
