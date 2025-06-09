# load_models.py

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, BertForSequenceClassification
from django.conf import settings
from huggingface_hub import hf_hub_download
HF_TOKEN = settings.HF_TOKEN


BASE_REPO = "mianyangacd/privacy-policy-spanbert"

'''
def load_model_and_tokenizer(subfolder, use_bert=False, use_token_classification=False):
    if use_token_classification:
        model = AutoModelForTokenClassification.from_pretrained(
            BASE_REPO,
            subfolder=subfolder,
            token=HF_TOKEN
        )
    elif use_bert:
        model = BertForSequenceClassification.from_pretrained(
            BASE_REPO,
            subfolder=subfolder,
            token=HF_TOKEN
        )
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            BASE_REPO,
            subfolder=subfolder,
            token=HF_TOKEN
        )

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_REPO,
        subfolder=subfolder,
        token=HF_TOKEN
    )
    model.eval()
    return model, tokenizer

'''




def load_model_and_tokenizer(subfolder, use_bert=False):
    if use_bert:
        model = BertForSequenceClassification.from_pretrained(
            BASE_REPO,
            subfolder=subfolder,
            token=HF_TOKEN
        )
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            BASE_REPO,
            subfolder=subfolder,
            token=HF_TOKEN
        )
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_REPO,
        subfolder=subfolder,
        token=HF_TOKEN
    )
    model.eval()
    return model, tokenizer

def load_label_mapping(subfolder):

    file_path = hf_hub_download(
        repo_id=BASE_REPO,
        filename="label_mapping.json",
        subfolder=subfolder,
        token=HF_TOKEN
    )
    with open(file_path, "r") as f:
        mapping = json.load(f)
    return {v: k for k, v in mapping.items()}
