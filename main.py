import os
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Optional
import io

app = FastAPI(title="Sentiment Intelligence API")
analyzer = SentimentIntensityAnalyzer()

# Improve VADER with app-specific negative terms
analyzer.lexicon.update({
    'buggy': -2.8,
    'bugs': -2.5,
    'slow': -2.0,
    'crash': -3.5,
    'crashing': -3.5,
    'unusable': -3.8,
    'broken': -3.2,
    'garbage': -3.5,
    'trash': -3.0,
    'worst': -3.5,
    'waste': -3.0,
    'useless': -3.5,
    'hanging': -2.5,
    'freezing': -2.5,
    'freeze': -2.5,
    'laggy': -2.5
})

# Helper for sentiment analysis
def get_sentiment(text: str):
    text_lower = text.lower()
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Base thresholds
    THRESHOLD = 0.15
    
    # User-requested neutral keywords and phrases
    neutral_items = [
        "okay", "fine", "average", "normal", "alright", "decent", "moderate", 
        "standard", "typical", "fair", "it's okay", "works fine", "nothing special", 
        "just normal", "average experience", "not bad", "not great either", 
        "does the job", "as expected", "fine for daily use", "it is okay", "it was okay"
    ]
    
    # Neutral patterns (e.g., "good but...")
    neutral_patterns = [
        "good but", "okay but", "works sometimes", "not bad but", "ok but", 
        "needs improvement", "better if", "not great but"
    ]
    
    has_neutral_keyword = any(k in text_lower for k in neutral_items)
    has_neutral_pattern = any(p in text_lower for p in neutral_patterns)
    
    # Strong negative words that should NEVER be neutral
    strong_negative_words = [
        "buggy", "slow", "crash", "unusable", "terrible", "worst", "garbage", 
        "trash", "broken", "useless", "hanging", "freezing", "freeze", "laggy", "bugs"
    ]
    has_strong_negative = any(n in text_lower for n in strong_negative_words)
    
    # Primary classification
    if scores['pos'] > 0.25 and scores['neg'] > 0.25:
        sentiment = "Mixed"
    elif compound >= THRESHOLD:
        sentiment = "Positive"
    elif compound <= -THRESHOLD:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
        
    # STRICT NEUTRAL OVERRIDE:
    # If it contains neutral keywords/patterns, we force Neutral unless it's extremely polar (>0.8)
    # OR if it contains strong negative feedback
    if sentiment != "Mixed" and (has_neutral_keyword or has_neutral_pattern) and abs(compound) < 0.85 and not has_strong_negative:
        sentiment = "Neutral"
    
    # Final check: If it has strong negative keywords but was classified as Neutral
    if sentiment == "Neutral" and has_strong_negative:
        sentiment = "Negative"

    # Confidence calculation
    if sentiment == "Mixed":
        conf_val = (scores['pos'] + scores['neg']) * 100 / 2 + 50
    elif sentiment == "Neutral":
        # Higher confidence if strictly forced by keywords/patterns
        if has_neutral_keyword or has_neutral_pattern:
            conf_val = 85.0 + (abs(compound) * 10)
        else:
            conf_val = (1 - (abs(compound) / 0.5)) * 100
    else:
        conf_val = abs(compound) * 100
        
    return {
        "text": text[:200] + "..." if len(text) > 200 else text,
        "sentiment": sentiment,
        "confidence": round(max(min(conf_val, 99.9), 50.0), 2),
        "scores": scores
    }

@app.post("/analyze")
async def analyze_text(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided")
    result = get_sentiment(text)
    return result

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename.lower()
    content = await file.read()
    reviews = []

    try:
        if filename.endswith(".txt"):
            text_content = content.decode("utf-8")
            reviews = [line.strip() for line in text_content.split("\n") if line.strip()]
        
        elif filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
            # Try to find a column with "review" or "text" or just use the first column
            target_col = None
            for col in df.columns:
                if "review" in col.lower() or "text" in col.lower():
                    target_col = col
                    break
            if target_col is None:
                target_col = df.columns[0]
            reviews = df[target_col].dropna().astype(str).tolist()

        elif filename.endswith(".json"):
            data = json.loads(content)
            if isinstance(data, list):
                reviews = [str(item) for item in data if item]
            elif isinstance(data, dict):
                # Look for a list in values
                for v in data.values():
                    if isinstance(v, list):
                        reviews = [str(item) for item in v if item]
                        break
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    if not reviews:
        return {"results": [], "summary": {"total": 0, "positive": 0, "negative": 0, "neutral": 0}}

    results = [get_sentiment(r) for r in reviews]
    
    summary = {
        "total": len(results),
        "positive": len([r for r in results if r["sentiment"] == "Positive"]),
        "negative": len([r for r in results if r["sentiment"] == "Negative"]),
        "neutral": len([r for r in results if r["sentiment"] == "Neutral"])
    }
    
    return {"results": results, "summary": summary}

# Mock data for initial load or demo
@app.get("/demo")
async def demo_data():
    sample_reviews = [
        "This product is amazing! I love how intuitive it is.",
        "Worst experience ever. The app crashed multiple times and the UI is terrible.",
        "It's okay, does what it says but nothing special.",
        "The standard version works as expected, no major issues.",
        "It was just fine. Not great, but not bad either.",
        "Decent value for the price, though the shipping was a bit slow.",
        "Average quality, mediocre performance.",
        "Excellent support, they were very helpful!"
    ]
    results = [get_sentiment(r) for r in sample_reviews]
    summary = {
        "total": len(results),
        "positive": len([r for r in results if r["sentiment"] == "Positive"]),
        "negative": len([r for r in results if r["sentiment"] == "Negative"]),
        "neutral": len([r for r in results if r["sentiment"] == "Neutral"])
    }
    return {"results": results, "summary": summary}

# Serving static files
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# Serve other static files
app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
