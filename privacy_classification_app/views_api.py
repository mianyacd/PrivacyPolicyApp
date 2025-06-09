'''
API for front end
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .model_runner import predict_paragraph_category
from .extraction_pipeline import extract_from_paragraph, get_attributes_for_label
from .span_model_runner import load_span_model
from .attribute_predictor import (
    predict_pit_value, predict_purpose_value,
    predict_does_not_label, predict_tpe_value
)
from .views import extract_paragraphs_from_url, get_display_attr, highlight_spans, is_real_span
import traceback

span_model, span_tokenizer = load_span_model()

#1. Classify, giving url, classify each paragraph with some labels
@method_decorator(csrf_exempt,name = 'dispatch')
class ClassifyURLView(APIView):
    def post(self, request):
        url = request.data.get("url")

        # ✅ URL 校验
        if not url or not isinstance(url, str):
            return Response({"error": "Missing or invalid 'url'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paragraphs = extract_paragraphs_from_url(url)
            result = []
            for para in paragraphs:
                labels = predict_paragraph_category(para)
                result.append({"text": para, "predicted_labels": labels})

            return Response({"paragraphs": result}, status=status.HTTP_200_OK)

        except Exception as e:
            # ✅ 返回详细错误信息用于调试（线上关闭）
            return Response({
                "error": "Failed to process URL",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#2. classify-paragraph, giving paragraph, make label prediction for this paragraph
@method_decorator(csrf_exempt, name='dispatch')
class ClassifyParagraphView(APIView):
    def post(self, request):
        paragraph = request.data.get("paragraph")
        if not paragraph:
            return Response({"error": "Missing 'paragraph'"}, status=status.HTTP_400_BAD_REQUEST)

        labels = predict_paragraph_category(paragraph)
        return Response({"paragraph": paragraph, "predicted_labels": labels})

# 3. extract attributes (full span info)
@method_decorator(csrf_exempt, name='dispatch')
class ExtractAttributesView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=400)

        paragraphs = extract_paragraphs_from_url(url)
        extracted_sentences = []

        for para in paragraphs:
            labels = predict_paragraph_category(para)
            extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)

            for sentence_item in extracted:
                cleaned_attributes = {
                    attr: [s for s in spans if is_real_span(s, sentence_item["sentence"])]
                    for attr, spans in sentence_item["attributes"].items()
                }
                sentence_item["attributes"] = cleaned_attributes

                sentence_item["highlighted_html"] = highlight_spans(
                    sentence_item["sentence"],
                    sentence_item["attributes"],
                    sentence_item["category"]
                )

                expected_attrs = get_attributes_for_label(sentence_item["category"])
                predicted_values = {}
                for attr in expected_attrs:
                    joined = ", ".join(sentence_item["attributes"].get(attr, []))
                    if attr == "Personal Information Type" and joined:
                        predicted_values[attr] = predict_pit_value(joined)
                    elif attr == "Purpose" and joined:
                        predicted_values[attr] = predict_purpose_value(joined)
                    elif attr == "Does/Does Not" and joined:
                        predicted_values[attr] = predict_does_not_label(joined)
                    elif attr == "Third Party Entity" and joined:
                        predicted_values[attr] = predict_tpe_value(joined)

                sentence_item["predicted_values"] = predicted_values

            extracted_sentences.extend(extracted)

        return Response({"sentences": extracted_sentences})


# 4. summarize personal information types
@method_decorator(csrf_exempt, name='dispatch')
class PersonalInfoSummaryView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=400)

        paragraphs = extract_paragraphs_from_url(url)
        personal_spans = []
        predicted_labels = []

        for para in paragraphs:
            labels = predict_paragraph_category(para)
            if "First Party Collection/Use" not in labels:
                continue

            extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)
            for item in extracted:
                spans = item["attributes"].get("Personal Information Type", [])
                if spans:
                    joined = ", ".join(spans)
                    label = predict_pit_value(joined)
                    personal_spans.append(joined)
                    predicted_labels.append(label)

        return Response({
            "personal_info_types": personal_spans,
            "predicted_categories": predicted_labels
        })


'''
Following code is previous code that only return pit for First Party Collection/Use
'''
'''

@method_decorator(csrf_exempt, name='dispatch')
class CollectedPersonalInfoView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url' in POST data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paragraphs = extract_paragraphs_from_url(url)
            collected_info_set = set()

            for para in paragraphs:
                labels = predict_paragraph_category(para)
                if "First Party Collection/Use" not in labels:
                    continue

                extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)
                for sentence_item in extracted:
                    if sentence_item["category"] != "First Party Collection/Use":
                        continue

                    attributes = sentence_item["attributes"]
                    sentence = sentence_item["sentence"]

                    # ✅ 检查是否为 "Does"
                    does_spans = attributes.get("Does/Does Not", [])
                    joined_does = ", ".join(does_spans)
                    if not joined_does or predict_does_not_label(joined_does) != "Does":
                        continue

                    # ✅ 对每个 PIT span 进行预测
                    for pit_span in attributes.get("Personal Information Type", []):
                        if is_real_span(pit_span, sentence):
                            predicted_value = predict_pit_value(pit_span)
                            collected_info_set.add(predicted_value)

            return Response({
                "url": url,
                "collected_personal_information": sorted(collected_info_set)
            })

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
'''

'''
Following code support both pit for First Party and Third Party
'''

@method_decorator(csrf_exempt, name='dispatch')
class CollectedPersonalInfoView(APIView):
    def post(self, request):
        url = request.data.get("url")
        include = request.data.get("include", ["first", "third"])
        include = [item.lower() for item in include]

        if not url:
            return Response({"error": "Missing 'url' in POST data."}, status=status.HTTP_400_BAD_REQUEST)


        allowed_values = {"first", "third"}
        invalid_values = [val for val in include if val not in allowed_values]
        if invalid_values:
            return Response({
                "error": "Invalid values in 'include' parameter.",
                "allowed_values": list(allowed_values),
                "invalid_values": invalid_values
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            paragraphs = extract_paragraphs_from_url(url)
            first_party_info = set()
            third_party_info = set()

            for para in paragraphs:
                labels = predict_paragraph_category(para)


                need_process = (
                    ("first" in include and "First Party Collection/Use" in labels) or
                    ("third" in include and "Third Party Sharing/Collection" in labels)
                )
                if not need_process:
                    continue

                extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)
                for sentence_item in extracted:
                    category = sentence_item["category"]
                    if category == "First Party Collection/Use" and "first" not in include:
                        continue
                    if category == "Third Party Sharing/Collection" and "third" not in include:
                        continue

                    attributes = sentence_item["attributes"]
                    sentence = sentence_item["sentence"]

                    does_spans = attributes.get("Does/Does Not", [])
                    joined_does = ", ".join(does_spans)
                    if not joined_does or predict_does_not_label(joined_does) != "Does":
                        continue

                    for pit_span in attributes.get("Personal Information Type", []):
                        if is_real_span(pit_span, sentence):
                            predicted_value = predict_pit_value(pit_span)
                            if category == "First Party Collection/Use":
                                first_party_info.add(predicted_value)
                            elif category == "Third Party Sharing/Collection":
                                third_party_info.add(predicted_value)

            response_data = {"url": url}
            if "first" in include:
                response_data["first_party_collected_personal_information"] = sorted(first_party_info)
            if "third" in include:
                response_data["third_party_collected_personal_information"] = sorted(third_party_info)

            return Response(response_data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
