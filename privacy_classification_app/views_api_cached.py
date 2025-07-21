"""
views_api_cached.py
改进版 API：支持缓存 + 返回完整结构化数据，供前端直接展示。
"""

import hashlib
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache

from .span_model_runner import load_span_model
from .extraction_pipeline import extract_from_paragraph, get_attributes_for_label
from .model_runner import predict_paragraph_category
from .attribute_predictor import (
    predict_pit_value, predict_purpose_value,
    predict_does_not_label, predict_tpe_value
)
from .views import extract_paragraphs_from_url, highlight_spans, is_real_span

# 加载Span模型（全局只加载一次）
span_model, span_tokenizer = load_span_model()


# 缓存Key生成
def make_key(prefix: str, text: str) -> str:
    return f"{prefix}:{hashlib.md5(text.encode()).hexdigest()}"


@method_decorator(csrf_exempt, name='dispatch')
class ExtractAttributesCachedView(APIView):
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=400)

        try:
            key = make_key("extract_attrs", url)
            cached_result = cache.get(key)
            if cached_result:
                return Response(cached_result)

            paragraphs = extract_paragraphs_from_url(url)

            result = {
                "url": url,
                "categories": {
                    "First Party Collection/Use": {"attributes": {}, "sentences": []},
                    "Third Party Sharing/Collection": {"attributes": {}, "sentences": []}
                }
            }

            for para in paragraphs:
                labels = predict_paragraph_category(para)
                extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)

                for sentence_item in extracted:
                    cat = sentence_item["category"]
                    if cat not in result["categories"]:
                        continue

                    # ✅ 清理 attributes
                    cleaned_attributes = {
                        attr: [s for s in spans if is_real_span(s, sentence_item["sentence"])]
                        for attr, spans in sentence_item["attributes"].items()
                    }
                    sentence_item["attributes"] = cleaned_attributes

                    # ✅ 预测属性值
                    expected_attrs = get_attributes_for_label(cat)
                    predicted_values = {}
                    for attr in expected_attrs:
                        joined = ", ".join(cleaned_attributes.get(attr, []))
                        if attr == "Personal Information Type" and joined:
                            predicted_values[attr] = predict_pit_value(joined)
                        elif attr == "Purpose" and joined:
                            predicted_values[attr] = predict_purpose_value(joined)
                        elif attr == "Does/Does Not" and joined:
                            predicted_values[attr] = predict_does_not_label(joined)
                        elif attr == "Third Party Entity" and joined:
                            predicted_values[attr] = predict_tpe_value(joined)

                    sentence_item["predicted_values"] = predicted_values

                    # ✅ 过滤逻辑：必须 Does 且有 PIT
                    if (
                            predicted_values.get("Does/Does Not") != "Does" or
                            not cleaned_attributes.get("Personal Information Type")  # 确保句子中确实有 PIT span
                    ):
                        continue

                    # ✅ 生成高亮 HTML
                    sentence_item["highlighted_html"] = highlight_spans(
                        sentence_item["sentence"], cleaned_attributes, cat, predicted_values
                    )

                    # ✅ 合并 attributes
                    for attr, spans in cleaned_attributes.items():
                        if attr not in result["categories"][cat]["attributes"]:
                            result["categories"][cat]["attributes"][attr] = []
                        result["categories"][cat]["attributes"][attr].extend(spans)

                    # 去重
                    for attr in result["categories"][cat]["attributes"]:
                        result["categories"][cat]["attributes"][attr] = list(
                            set(result["categories"][cat]["attributes"][attr])
                        )

                    result["categories"][cat]["sentences"].append(sentence_item)

            cache.set(key, result, timeout=3600)
            return Response(result)

        except Exception as e:
            return Response({
                "error": "Failed to process URL",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=500)

'''
@method_decorator(csrf_exempt, name='dispatch')
class CollectedAndSharedPersonalInfoView(APIView):
    """
    输入：隐私政策URL
    输出：First Party收集的Personal Information + Third Party共享的Personal Information
    """
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=400)

        try:
            key = make_key("collected_shared_pit", url)
            cached_result = cache.get(key)
            if cached_result:
                return Response(cached_result)

            # 初始化结果
            first_party_set = set()
            third_party_set = set()

            # 提取段落
            paragraphs = extract_paragraphs_from_url(url)

            for para in paragraphs:
                labels = predict_paragraph_category(para)
                if not any(lbl in ["First Party Collection/Use", "Third Party Sharing/Collection"] for lbl in labels):
                    continue

                extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)

                for sentence_item in extracted:
                    category = sentence_item.get("category")
                    attributes = sentence_item.get("attributes", {})
                    sentence = sentence_item.get("sentence", "")

                    # ✅ First Party
                    if category == "First Party Collection/Use":
                        # 检查 Does/Does Not
                        does_spans = attributes.get("Does/Does Not", [])
                        joined_does = ", ".join(does_spans)
                        if not joined_does or predict_does_not_label(joined_does) != "Does":
                            continue

                        # 提取 PIT
                        for pit_span in attributes.get("Personal Information Type", []):
                            if is_real_span(pit_span, sentence):
                                predicted_value = predict_pit_value(pit_span)
                                first_party_set.add(predicted_value)

                    # ✅ Third Party
                    if category == "Third Party Sharing/Collection":
                        for pit_span in attributes.get("Personal Information Type", []):
                            if is_real_span(pit_span, sentence):
                                predicted_value = predict_pit_value(pit_span)
                                third_party_set.add(predicted_value)

            result = {
                "url": url,
                "first_party_collected": sorted(first_party_set),
                "third_party_shared": sorted(third_party_set)
            }

            cache.set(key, result, timeout=3600)  # 缓存1小时
            return Response(result)

        except Exception as e:
            return Response({
                "error": "Failed to process URL",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=500)
'''

'''以下修改用来看看输出的attribute是不是找到对应的text span
@method_decorator(csrf_exempt, name='dispatch')
class CollectedAndSharedDetailedView(APIView):
    """
    输入：隐私政策 URL
    输出：First Party & Third Party 的 Personal Information，附：
      - 原始 span
      - 原始句子
      - Does/Does Not（值 + span）
      - Purpose（值 + span）
    """
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=400)

        try:
            key = make_key("collected_shared_detailed", url)
            cached_result = cache.get(key)
            if cached_result:
                return Response(cached_result)

            # ✅ dict: {attribute: set((span, sentence, does_value, does_span, purpose_value, purpose_span))}
            first_party_map = {}
            third_party_map = {}

            paragraphs = extract_paragraphs_from_url(url)

            for para in paragraphs:
                labels = predict_paragraph_category(para)
                if not any(lbl in ["First Party Collection/Use", "Third Party Sharing/Collection"] for lbl in labels):
                    continue

                extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)

                for sentence_item in extracted:
                    category = sentence_item.get("category")
                    attributes = sentence_item.get("attributes", {})
                    sentence = sentence_item.get("sentence", "")

                    # ✅ Does/Does Not
                    does_spans = attributes.get("Does/Does Not", [])
                    does_text_span = does_spans[0] if does_spans else None
                    does_value = predict_does_not_label(", ".join(does_spans)) if does_spans else "Unknown"

                    # ✅ Purpose
                    purpose_spans = attributes.get("Purpose", [])
                    purpose_text_span = purpose_spans[0] if purpose_spans else None
                    purpose_value = predict_purpose_value(purpose_text_span) if purpose_text_span else "Unknown"

                    # ✅ Personal Information Type
                    for pit_span in attributes.get("Personal Information Type", []):
                        if is_real_span(pit_span, sentence):
                            predicted_value = predict_pit_value(pit_span)
                            detail_tuple = (
                                pit_span, sentence, does_value, does_text_span, purpose_value, purpose_text_span
                            )

                            if category == "First Party Collection/Use":
                                # 仅保留 Does 的情况
                                if does_value == "Does":
                                    first_party_map.setdefault(predicted_value, set()).add(detail_tuple)

                            elif category == "Third Party Sharing/Collection":
                                third_party_map.setdefault(predicted_value, set()).add(detail_tuple)

            # ✅ 格式化输出
            def format_details(data_map):
                return [
                    {
                        "attribute": attr,
                        "details": [
                            {
                                "span": span,
                                "sentence": sent,
                                "does_or_not": {"value": does_val, "span": does_span},
                                "purpose": {"value": purpose_val, "span": purpose_span}
                            }
                            for (span, sent, does_val, does_span, purpose_val, purpose_span) in sorted(pairs)
                        ]
                    }
                    for attr, pairs in data_map.items()
                ]

            result = {
                "url": url,
                "first_party_collected": format_details(first_party_map),
                "third_party_shared": format_details(third_party_map)
            }

            cache.set(key, result, timeout=3600)
            return Response(result)

        except Exception as e:
            return Response({
                "error": "Failed to process URL",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=500)
'''

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import PolicyCache
from .utils import extract_last_updated
from .services.privacy_pipeline import run_privacy_pipeline
import traceback

@method_decorator(csrf_exempt, name='dispatch')
class CollectedAndSharedDetailedView(APIView):
    """
    输入: 隐私策略 URL
    输出: First Party & Third Party 的 Personal Information (带缓存)
    缓存逻辑:
        - 如果 URL 存在并且 last_updated_date 一致，返回缓存
        - 否则调用 pipeline 处理，并更新缓存
    """
    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "Missing 'url'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 检查缓存
            cached_entry = PolicyCache.objects.filter(url=url).first()
            latest_date = extract_last_updated(url)

            if cached_entry and cached_entry.last_updated_date == latest_date:
                return Response(cached_entry.cached_result)

            # 重新跑 pipeline
            result = run_privacy_pipeline(url)

            # 更新缓存
            if cached_entry:
                cached_entry.cached_result = result
                cached_entry.last_updated_date = latest_date
                cached_entry.save()
            else:
                PolicyCache.objects.create(
                    url=url,
                    last_updated_date=latest_date,
                    cached_result=result
                )

            return Response(result)

        except Exception as e:
            return Response({
                "error": "Failed to process URL",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
