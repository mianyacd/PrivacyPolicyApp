import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

'''
Followings are for local deployment

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_path = "fine_tuned_bert_5"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.to(device)
model.eval()
'''
from django.conf import settings
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BASE_REPO = "mianyangacd/privacy-policy-spanbert"
SUBFOLDER = "fine_tuned_bert_5"
HF_TOKEN = settings.HF_TOKEN

tokenizer = AutoTokenizer.from_pretrained(
    BASE_REPO,
    subfolder=SUBFOLDER,
    token=HF_TOKEN
)
model = AutoModelForSequenceClassification.from_pretrained(
    BASE_REPO,
    subfolder=SUBFOLDER,
    token=HF_TOKEN
)

model.to(device)
model.eval()

'''
category labels sequences are matters!!
here the sequences follow what we have on colab
This category_labels is a list of true labels
dynamically extracted from the training data in a stable order.
'''
category_labels = [
    "Data Retention",
    "Data Security",
    "Do Not Track",
    "First Party Collection/Use",
    "International and Specific Audiences",
    "Other",
    "Policy Change",
    "Third Party Sharing/Collection",
    "User Access, Edit and Deletion",
    "User Choice/Control"
]

def predict_paragraph_category(paragraph, threshold=0.5):
    inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {key: val.to(device) for key, val in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probs = torch.sigmoid(logits).cpu().numpy()[0]
    preds = (probs > threshold).astype(int)

    predicted = [category_labels[i] for i in range(len(category_labels)) if preds[i] == 1]
    return predicted if predicted else ["None"]