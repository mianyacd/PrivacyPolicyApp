import spacy
nlp = spacy.load("en_core_web_sm")
from .span_model_runner import run_span_model, load_span_model

span_model, span_tokenizer = load_span_model()

FIRST_PARTY_ATTRS = ["Does/Does Not", "Personal Information Type", "Purpose"]
THIRD_PARTY_ATTRS = ["Personal Information Type", "Does/Does Not", "Third Party Entity", "Purpose"]

def split_into_sentences(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]



def is_target_paragraph(label_list):
    return ("First Party Collection/Use" in label_list) or ("Third Party Sharing/Collection" in label_list)

def get_attributes_for_label(label):
    if label == "First Party Collection/Use":
        return FIRST_PARTY_ATTRS
    elif label == "Third Party Sharing/Collection":
        return THIRD_PARTY_ATTRS
    return []

def extract_from_paragraph(paragraph_text, labels, model, tokenizer):
    results = []

    target_labels = [l for l in labels if l in ["First Party Collection/Use", "Third Party Sharing/Collection"]]
    if not target_labels:
        return results

    sentences = split_into_sentences(paragraph_text)

    for sentence in sentences:
        for label in target_labels:
            attributes = get_attributes_for_label(label)
            spans = run_span_model(sentence, label, attributes, model, tokenizer)
            results.append({
                "sentence": sentence,
                "category": label,
                "attributes": spans
            })
    return results

