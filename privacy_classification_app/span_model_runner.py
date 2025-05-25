from transformers import AutoModelForQuestionAnswering, AutoTokenizer, AutoModelForTokenClassification
import torch
'''
following code for local deployment:


def load_span_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForQuestionAnswering.from_pretrained(model_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    return model, tokenizer
'''
from django.conf import settings
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

BASE_REPO = "mianyangacd/privacy-policy-spanbert"
SUBFOLDER = "spanbert-finetuned"
HF_TOKEN = settings.HF_TOKEN

def load_span_model():
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_REPO,
        subfolder=SUBFOLDER,
        token=HF_TOKEN
    )
    model = AutoModelForTokenClassification.from_pretrained(
        BASE_REPO,
        subfolder=SUBFOLDER,
        token=HF_TOKEN
    )
    model.to(device)
    model.eval()
    return model, tokenizer


def run_span_model(sentence, category_label, attribute_list, model, tokenizer):
    """
    对一个句子和它的 label 分类下要提取的属性，挨个提问，抽取 span。
    """
    results = {}

    for attr in attribute_list:
        question = f"What part of the text refers to {attr}?"

        # Tokenize with offset mapping for answer span
        encoded = tokenizer(
            question, sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_offsets_mapping=True
        )

        offset_mapping = encoded.pop("offset_mapping")[0].tolist()

        with torch.no_grad():
            outputs = model(**encoded)

        start_idx = torch.argmax(outputs.start_logits).item()
        end_idx = torch.argmax(outputs.end_logits).item() + 1

        # Convert tokens to string span
        span_tokens = encoded["input_ids"][0][start_idx:end_idx]
        span_text = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(span_tokens))

        if span_text.strip() and span_text.lower().strip() != question.lower().strip():
            results[attr] = [span_text]
        else:
            results[attr] = []

        # Optionally: get exact character start/end from offset mapping
        char_start = offset_mapping[start_idx][0]
        char_end = offset_mapping[end_idx - 1][1]

        results[attr] = [span_text] if span_text.strip() else []

    return results

