import re


def external_content_penalty(answer, retrieved_chunks):
    """
    Penalizes if answer contains content not appearing
    in any retrieved chunk.
    """

    corpus_text = " ".join(retrieved_chunks).lower()
    answer_lower = answer.lower()

    penalty = 0.0

    # Check numeric claims
    numbers = re.findall(r'\d+', answer_lower)

    for num in numbers:
        if num not in corpus_text:
            penalty += 0.05

    # Check suspicious keywords
    suspicious_sources = [
        # English
        "who", "world health organization", "cdc", "centers for disease control",
        "unicef", "un", "united nations", "world bank", "imf", "international monetary fund",
        "fao", "food and agriculture organization", "unesco", "nih", "national institutes of health",
        "fda", "food and drug administration", "ema", "european medicines agency",
        "lancet", "nature", "nejm", "new england journal of medicine",
        "global health observatory", "global data", "un report", "who report",
        "cdc report", "unicef report", "world bank report",
        
        # Sinhala
        "විශ්ව සෞඛ්‍ය සංවිධානය", "විශ්ව සෞඛ්‍ය", "එ.ජ.", "එක්සත් ජාතික",
        "විශ්ව බැංකුව", "ජාත්‍යන්තර මූල්‍ය අරමුදල්", "යුනිසෙෆ්",
        "ජාත්‍යන්තර ආහාර සහ කෘෂිකාර්මික සංවිධානය", "යුනෙස්කෝ",
        "ජාත්‍යන්තර සෞඛ්‍ය පැවැත්වීමේ මධ්‍යස්ථානය", "ආහාර සහ ඖෂධ පරිපාලනය",
        "යුරෝපීය ඖෂධ පරිපාලනය", "ලැන්සට්", "නේචර්", "එන්ජේඑම්",
        "විශ්ව සෞඛ්‍ය නිරීක්ෂණාගාරය", "එ.ජ. වාර්තාව", "විශ්ව සෞඛ්‍ය වාර්තාව",
        
        # Tamil
        "உலக சுகாதார அமைப்பு", "உலக சுகாதாரம்", "ஐ.நா.", "ஐக்கிய நாடுகள்",
        "உலக வங்கி", "சர்வதேச நிதிய நிறுவனம்", "யூனிசெஃப்",
        "சர்வதேச உணவு மற்றும் விவசாய அமைப்பு", "யூனெஸ்கோ",
        "தேசிய சுகாதார நிறுவனங்கள்", "உணவு மற்றும் மருந்து நிர்வாகம்",
        "ஐரோப்பிய மருந்து நிறுவனம்", "லான்செட்", "நேச்சர்", "என்ஜேஎம்",
        "உலக சுகாதார கண்காணிப்பு", "ஐ.நா. அறிக்கை", "உலக சுகாதார அறிக்கை"
    ]

    for word in suspicious_sources:
        if word in answer_lower and word not in corpus_text:
            penalty += 0.1

    return min(penalty, 0.3)