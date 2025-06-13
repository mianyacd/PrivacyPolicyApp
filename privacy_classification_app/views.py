from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from bs4 import BeautifulSoup

from .model_runner import predict_paragraph_category
from django.shortcuts import render
from collections import Counter
import matplotlib.pyplot as plt
import os
import uuid

from .extraction_pipeline import extract_from_paragraph,get_attributes_for_label
from .span_model_runner import load_span_model
import re

from .attribute_predictor import predict_pit_value, predict_purpose_value, predict_does_not_label, predict_tpe_value

span_model, span_tokenizer = load_span_model()

def get_display_attr(attr,category):
    if attr == "Action Third Party" and category == "First Party Collection/Use":
        return "Action First Party"
    return attr




import re

def highlight_spans(sentence, attributes, category_label):
    span_map = []

    for attr, spans in attributes.items():
        css_class = (
            "action-first-party" if category_label == "First Party Collection/Use" and attr == "Action Third Party"
            else attr.lower().replace(" ", "-")
        )
        for span in spans:
            if not span or not span.strip():
                continue
            cleaned = span.strip()
            span_map.append((cleaned, css_class))

    span_map = sorted(span_map, key=lambda x: -len(x[0]))

    for text, css_class in span_map:
        pattern = re.compile(re.escape(text), re.IGNORECASE)
        sentence = pattern.sub(
            lambda m: f'<mark class="{css_class}">{m.group(0)}</mark>',
            sentence,
            count=1
        )

    return sentence





def is_real_span(span,sentence):
    return span.strip().lower() in sentence.lower()

def extract_attributes_view(request):
    if request.method == "POST":
        url = request.POST.get("url")
        paragraphs = extract_paragraphs_from_url(url)
        results = []
        extracted_sentences = []

        for para in paragraphs:
            labels = predict_paragraph_category(para)
            results.append({"text": para, "labels": labels})

            extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)

            for sentence_item in extracted:
                # ✅ 去除伪 span（例如 "what part of the text refers to purpose"）
                cleaned_attributes = {}
                for attr, spans in sentence_item["attributes"].items():
                    real_spans = [s for s in spans if is_real_span(s, sentence_item["sentence"])]
                    if real_spans:
                        cleaned_attributes[attr] = real_spans
                sentence_item["attributes"] = cleaned_attributes

                # ✅ 高亮 + 展示 friendly 名称
                sentence_item["highlighted"] = highlight_spans(
                    sentence_item["sentence"],
                    sentence_item["attributes"],
                    sentence_item["category"]
                )


                expected_attrs = get_attributes_for_label(sentence_item["category"])


                display_attributes = {}
                for attr in expected_attrs:
                    display_name = get_display_attr(attr, sentence_item["category"])
                    spans = sentence_item["attributes"].get(attr, [])


                    if attr == "Personal Information Type" and spans:
                        joined_span = ", ".join(spans)
                        predicted = predict_pit_value(joined_span)
                        display_attributes[display_name] = [f"{joined_span} [Predicted: {predicted}]"]

                    elif attr == "Purpose" and spans:
                        joined_span = ", ".join(spans)
                        predicted = predict_purpose_value(joined_span)
                        display_attributes[display_name] = [f"{joined_span} [Predicted: {predicted}]"]

                    elif attr == "Does/Does Not" and spans:
                        joined_span = ", ".join(spans)
                        predicted = predict_does_not_label(joined_span)
                        display_attributes[display_name] = [f"{joined_span} [Predicted: {predicted}]"]

                    elif attr == "Third Party Entity" and spans:
                        joined_span = ", ".join(spans)
                        predicted = predict_tpe_value(joined_span)
                        display_attributes[display_name] = [f"{joined_span} [Predicted: {predicted}]"]
                    else:
                        display_attributes[display_name] = spans

                sentence_item["display_attributes"] = display_attributes

            extracted_sentences.extend(extracted)

        print("Extracted Sentences Count:", len(extracted_sentences))
        return render(request, "privacy_classification_app/attribute_results.html", {
            "url": url,
            "extracted_sentences": extracted_sentences,
        })

    # GET 请求情况（从 classify-ui 跳转）
    default_url = request.GET.get("url", "")
    return render(request, "privacy_classification_app/input_attribute_url.html", {
        "default_url": default_url
    })



#Extract the paragraph from url
def extract_paragraphs_from_url(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    return [p for p in paragraphs if len(p) > 30]

def classify_and_show(request):
    if request.method == "POST":
        url = request.POST.get("url")
        paragraphs = extract_paragraphs_from_url(url)
        results = []
        all_labels = []

        for para in paragraphs:
            labels = predict_paragraph_category(para)
            results.append({"text": para, "labels": labels})
            all_labels.extend(labels)

        # 统计标签频次
        label_counts = Counter(all_labels)
        labels = list(label_counts.keys())
        counts = list(label_counts.values())

        # 生成条形图并保存为静态文件
        filename = f"{uuid.uuid4()}.png"
        save_path = os.path.join("privacy_classification_app", "static", filename)
        plt.figure(figsize=(10, 5))
        plt.bar(labels, counts, color='skyblue')
        plt.title("Label Distribution")
        plt.xticks(rotation=30, ha='right', fontsize=10, wrap=True)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

        return render(request, "privacy_classification_app/show_results.html", {
            "results": results,
            "chart_file": filename,
            "url":url
        })

    return render(request, "privacy_classification_app/input_url.html")

#View of API
class ClassifyPolicyView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paragraphs = extract_paragraphs_from_url(url)
            results = []
            for para in paragraphs:
                predicted_labels = predict_paragraph_category(para)
                results.append({
                    "paragraph": para,
                    "predicted_labels": predicted_labels
                })
            return Response({"results": results})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClassifyParagraphView(APIView):
    def post(self, request):
        paragraph = request.data.get("paragraph")
        if not paragraph:
            return Response({"error": "Missing 'paragraph'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            predicted_labels = predict_paragraph_category(paragraph)
            return Response({
                "paragraph": paragraph,
                "predicted_labels": predicted_labels
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def test_filter_sentences_page(request):
    return render(request, 'privacy_classification_app/test_filter_sentences.html')