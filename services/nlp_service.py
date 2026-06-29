import re
from collections import Counter

try:
    import spacy
    from spacy.pipeline import EntityRuler

    try:
        nlp = spacy.load("en_core_web_sm")

        if "finance_org_ruler" not in nlp.pipe_names:
            ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True}, name="finance_org_ruler")
            ruler.add_patterns([
                {"label": "ORG", "pattern": "central bank"},
                {"label": "ORG", "pattern": "federal reserve"},
                {"label": "ORG", "pattern": "reserve bank of india"},
                {"label": "ORG", "pattern": "rbi"},
                {"label": "ORG", "pattern": "european central bank"},
                {"label": "ORG", "pattern": "ecb"},
                {"label": "ORG", "pattern": "imf"},
                {"label": "ORG", "pattern": "world bank"},
                {"label": "ORG", "pattern": "goldman sachs"},
                {"label": "ORG", "pattern": "morgan stanley"},
                {"label": "ORG", "pattern": "jp morgan"},
                {"label": "ORG", "pattern": "jpmorgan"},
                {"label": "ORG", "pattern": "hsbc"},
                {"label": "ORG", "pattern": "citibank"},
                {"label": "ORG", "pattern": "hdfc"},
                {"label": "ORG", "pattern": "icici"},
                {"label": "ORG", "pattern": "sebi"},
                {"label": "ORG", "pattern": "nse"},
                {"label": "ORG", "pattern": "bse"}
            ])
    except Exception:
        nlp = None
except Exception:
    nlp = None


POSITIVE_WORDS = {
    "growth", "gain", "gains", "bullish", "rally", "support", "improving",
    "strong", "surge", "upside", "optimistic", "recovery", "expansion",
    "liquidity", "easing", "stability", "stable", "positive"
}

NEGATIVE_WORDS = {
    "fall", "decline", "loss", "losses", "bearish", "drop", "stress",
    "inflation", "volatility", "weak", "downturn", "recession", "risk",
    "tightening", "negative", "slowdown", "uncertainty", "crisis"
}

CATEGORY_KEYWORDS = {
    "macro_economy": {
        "inflation", "gdp", "growth", "recession", "economy", "liquidity",
        "rates", "interest", "central", "bank", "policy"
    },
    "equity_market": {
        "stocks", "equity", "shares", "market", "index", "bullish", "bearish",
        "valuation", "earnings", "rally"
    },
    "fixed_income": {
        "bond", "yield", "debt", "treasury", "coupon", "duration"
    },
    "commodities": {
        "gold", "oil", "commodity", "silver", "energy"
    },
    "general_finance": {
        "investment", "portfolio", "returns", "risk", "wealth", "finance"
    }
}

FINANCE_TERMS = {
    "central bank", "federal reserve", "reserve bank", "reserve bank of india",
    "rbi", "ecb", "european central bank", "imf", "world bank",
    "stock market", "bond market", "equity market", "interest rates",
    "inflation", "liquidity", "growth outlook", "market outlook",
    "economic growth", "treasury yields"
}

ORG_PATTERNS = [
    r"\bCentral Bank\b",
    r"\bFederal Reserve\b",
    r"\bReserve Bank of India\b",
    r"\bRBI\b",
    r"\bEuropean Central Bank\b",
    r"\bECB\b",
    r"\bIMF\b",
    r"\bWorld Bank\b",
    r"\bGoldman Sachs\b",
    r"\bMorgan Stanley\b",
    r"\bJP Morgan\b",
    r"\bJPMorgan\b",
    r"\bHSBC\b",
    r"\bCitibank\b",
    r"\bICICI\b",
    r"\bHDFC\b",
    r"\bSEBI\b",
    r"\bNSE\b",
    r"\bBSE\b"
]

ORG_FALLBACK_TERMS = {
    "central bank",
    "federal reserve",
    "reserve bank",
    "reserve bank of india",
    "european central bank",
    "world bank",
    "imf",
    "rbi",
    "ecb"
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "to", "of", "in", "on",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "as", "at", "it", "its", "into",
    "about", "than", "then", "over", "under", "after", "before", "during",
    "signals", "signal"
}


def normalize_text(text):
    text = text or ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text):
    return re.findall(r"\b[a-zA-Z][a-zA-Z\-]+\b", text.lower())


def detect_sentiment(tokens):
    pos = sum(1 for token in tokens if token in POSITIVE_WORDS)
    neg = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    score = pos - neg

    if score > 0:
        sentiment = "Positive"
    elif score < 0:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment, score, pos, neg


def detect_category(tokens):
    token_set = set(tokens)
    scores = {}

    for category, words in CATEGORY_KEYWORDS.items():
        scores[category] = len(token_set.intersection(words))

    best_category = max(scores, key=scores.get) if scores else "general_finance"
    if scores.get(best_category, 0) == 0:
        best_category = "general_finance"

    return best_category, scores


def extract_keywords(tokens, text, max_keywords=5):
    candidates = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq = Counter(candidates)

    phrase_hits = []
    lower_text = text.lower()
    for term in FINANCE_TERMS:
        if term in lower_text:
            phrase_hits.append(term)

    ranked_words = [word for word, _ in freq.most_common(10)]

    combined = []
    for item in phrase_hits + ranked_words:
        if item not in combined:
            combined.append(item)

    return combined[:max_keywords]


def dedupe_preserve_case(items):
    seen = set()
    result = []

    for item in items:
        cleaned = item.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def extract_entities(text):
    organizations = []
    economic_terms = []
    financial_assets = []
    numeric_values = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)

    lower_text = text.lower()

    for term in FINANCE_TERMS:
        if term in lower_text:
            economic_terms.append(term)

    asset_terms = ["gold", "oil", "bond", "equity", "stocks", "cash", "debt"]
    for asset in asset_terms:
        if asset in lower_text:
            financial_assets.append(asset)

    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                organizations.append(ent.text.strip())

    for pattern in ORG_PATTERNS:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            organizations.append(match.strip())

    for fallback_term in ORG_FALLBACK_TERMS:
        if fallback_term in lower_text:
            organizations.append(fallback_term.title())

    organizations = dedupe_preserve_case(organizations)

    return {
        "organizations": organizations,
        "economic_terms": dedupe_preserve_case(economic_terms),
        "financial_assets": dedupe_preserve_case(financial_assets),
        "numeric_values": numeric_values
    }


def summarize_text(text, keywords, sentiment, category):
    if not text:
        return ""

    keyword_text = ", ".join(keywords[:3]) if keywords else "general market factors"

    return (
        f"The text reflects a {sentiment.lower()} market tone in the {category.replace('_', ' ')} space, "
        f"with focus on {keyword_text}."
    )


def analyze_text(text):
    original_text = text or ""
    cleaned_text = normalize_text(original_text)
    tokens = tokenize(cleaned_text)

    sentiment, sentiment_score, positive_matches, negative_matches = detect_sentiment(tokens)
    category, category_scores = detect_category(tokens)
    keywords = extract_keywords(tokens, cleaned_text)
    entities = extract_entities(cleaned_text)
    summary = summarize_text(cleaned_text, keywords, sentiment, category)

    return {
        "original_text": original_text,
        "preprocessing": {
            "original_length": len(original_text),
            "token_count": len(tokens),
            "normalized": True,
            "special_characters_removed": True
        },
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "positive_matches": positive_matches,
        "negative_matches": negative_matches,
        "category": category,
        "category_scores": category_scores,
        "keywords": keywords,
        "entities": entities,
        "summary": summary
    }


def get_nlp_evidence_bundle(text):
    result = analyze_text(text)

    return {
        "input_text": text,
        "preprocessing": result["preprocessing"],
        "sentiment_evidence": {
            "sentiment": result["sentiment"],
            "score": result["sentiment_score"],
            "positive_matches": result["positive_matches"],
            "negative_matches": result["negative_matches"]
        },
        "category_evidence": {
            "category": result["category"],
            "scores": result["category_scores"]
        },
        "keywords": result["keywords"],
        "entities": result["entities"],
        "summary": result["summary"]
    }