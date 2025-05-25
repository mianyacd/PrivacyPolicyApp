import torch
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification,BertForSequenceClassification
'''
for deployment
'''
from .load_models import load_model_and_tokenizer,load_label_mapping

pit_model, pit_tokenizer = load_model_and_tokenizer("PIT_fine_tuned_bert")
purpose_model, purpose_tokenizer = load_model_and_tokenizer("PP_fine_tuned_bert")
tpe_model, tpe_tokenizer = load_model_and_tokenizer("TPE_fine_tuned_bert")
ddn_model, ddn_tokenizer = load_model_and_tokenizer("DDN_fine_tuned_bert", use_bert=True)

id_to_pit_label = load_label_mapping("PIT_fine_tuned_bert")
id_to_purpose_label = load_label_mapping("PP_fine_tuned_bert")
id_to_tpe_label = load_label_mapping("TPE_fine_tuned_bert")
'''
above change for online deployment
'''

'''
Hide following code
They are for local deployment test



PIT_MODEL_PATH = "PIT_fine_tuned_bert"
PURPOSE_MODEL_PATH = "PP_fine_tuned_bert"
TPE_MODEL_PATH = "TPE_fine_tuned_bert"
DDN_MODEL_PATH = "DDN_fine_tuned_bert"


pit_tokenizer = AutoTokenizer.from_pretrained(PIT_MODEL_PATH)
pit_model = AutoModelForSequenceClassification.from_pretrained(PIT_MODEL_PATH)
pit_model.eval()

purpose_tokenizer = AutoTokenizer.from_pretrained(PURPOSE_MODEL_PATH)
purpose_model = AutoModelForSequenceClassification.from_pretrained(PURPOSE_MODEL_PATH)
purpose_model.eval()

tpe_tokenizer = AutoTokenizer.from_pretrained(TPE_MODEL_PATH)
tpe_model = AutoModelForSequenceClassification.from_pretrained(TPE_MODEL_PATH)
tpe_model.eval()

ddn_tokenizer = AutoTokenizer.from_pretrained(DDN_MODEL_PATH)
ddn_model = BertForSequenceClassification.from_pretrained(DDN_MODEL_PATH)
ddn_model.eval()
'''

#mapping of ddn
ddn_id_to_label = {
    0: "Does",
    1: "Does Not"
}

def predict_does_not_label(span_text: str) -> str:
    inputs = ddn_tokenizer(span_text, return_tensors="pt", padding=True, truncation=True, max_length=128)

    with torch.no_grad():
        outputs = ddn_model(**inputs)
        pred_id = torch.argmax(outputs.logits).item()

    return ddn_id_to_label.get(pred_id, "Unknown")

'''
Hide following code
They are for local deployment test


with open(f"{PIT_MODEL_PATH}/label_mapping.json", "r") as f:
    pit_label_mapping = json.load(f)

id_to_pit_label = {v: k for k, v in pit_label_mapping.items()}

with open(f"{PURPOSE_MODEL_PATH}/label_mapping.json", "r") as f:
    purpose_label_mapping = json.load(f)
id_to_purpose_label = {v: k for k, v in purpose_label_mapping.items()}

with open(f"{TPE_MODEL_PATH}/label_mapping.json", "r") as f:
    tpe_label_mapping = json.load(f)
id_to_tpe_label = {v: k for k, v in tpe_label_mapping.items()}
'''
def predict_tpe_value(text_span: str) -> str:
    encoding = tpe_tokenizer(
        text_span,
        padding="max_length",
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )
    with torch.no_grad():
        outputs = tpe_model(**encoding)
        predicted_label_id = torch.argmax(outputs.logits, dim=1).item()
    return id_to_tpe_label.get(predicted_label_id, "unknown")


def predict_pit_value(text_span: str) -> str:
    encoding = pit_tokenizer(
        text_span,
        padding="max_length",
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )
    with torch.no_grad():
        outputs = pit_model(**encoding)
        predicted_label_id = torch.argmax(outputs.logits, dim=1).item()
    return id_to_pit_label.get(predicted_label_id, "unknown")


def predict_purpose_value(text_span: str) -> str:
    encoding = purpose_tokenizer(
        text_span,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    with torch.no_grad():
        outputs = purpose_model(**encoding)
        predicted_label_id = torch.argmax(outputs.logits, dim=1).item()
    return id_to_purpose_label.get(predicted_label_id, "unknown")