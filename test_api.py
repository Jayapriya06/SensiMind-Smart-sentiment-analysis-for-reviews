import requests

BASE_URL = "http://localhost:8000"

def test_mixed_sentiment():
    test_cases = [
        "I love the design, but the battery life is terrible.",
        "Beautiful scenery, though the hotel was a dump.",
        "The app is great but it crashes constantly.",
        "Good food, bad service."
    ]
    
    print("Testing Mixed Sentiment Detection:")
    for text in test_cases:
        r = requests.post(f"{BASE_URL}/analyze", data={"text": text})
        data = r.json()
        print(f"Text: '{text}' -> Result: {data['sentiment']} (Conf: {data['confidence']})")
        print(f"  Scores: {data['scores']}")

if __name__ == "__main__":
    test_mixed_sentiment()
