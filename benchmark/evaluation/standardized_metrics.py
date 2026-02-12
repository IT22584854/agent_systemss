import nltk
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer

nltk.download('punkt')

def standardized_scores(reference, prediction):
    bleu = sentence_bleu([reference.split()], prediction.split())

    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    rouge = scorer.score(reference, prediction)['rougeL'].fmeasure

    return {
        "bleu": bleu,
        "rougeL": rouge,
        "standardized_score": (bleu + rouge) / 2
    }
