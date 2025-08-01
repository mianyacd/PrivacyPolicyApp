# privacy_classification_app/services/analysis_manager.py

from ..models import PolicyCache, AnalyzedSentence
from ..utils import extract_last_updated
from .privacy_pipeline import run_privacy_pipeline

def analyze_and_store_pipeline(url):
    last_updated = extract_last_updated(url)

    cached = PolicyCache.objects.filter(url=url).first()
    if cached and cached.last_updated_date == last_updated:
        return cached.cached_result

    # 分析隐私政策
    result = run_privacy_pipeline(url)

    # 更新 PolicyCache
    if cached:
        cached.cached_result = result
        cached.last_updated_date = last_updated
        cached.save()
    else:
        PolicyCache.objects.create(
            url=url,
            cached_result=result,
            last_updated_date=last_updated
        )

    # 存入 AnalyzedSentence 表
    AnalyzedSentence.objects.filter(url=url).delete()

    for category_block in result.get("categories", {}).values():
        for sentence_item in category_block.get("sentences", []):
            sentence = sentence_item.get("sentence")
            attributes = sentence_item.get("attributes", {})
            predicted_values = sentence_item.get("predicted_values", {})

            for attr, spans in attributes.items():
                for span in spans:
                    AnalyzedSentence.objects.create(
                        url=url,
                        category=sentence_item.get("category"),
                        sentence=sentence,
                        attribute=attr,
                        span=span,
                        predicted_value=predicted_values.get(attr),
                        does_or_not_value=predicted_values.get("Does/Does Not") if attr == "Personal Information Type" else None,
                        does_or_not_span=next(iter(attributes.get("Does/Does Not", [])), None) if attr == "Personal Information Type" else None,
                        purpose_value=predicted_values.get("Purpose") if attr == "Personal Information Type" else None,
                        purpose_span=next(iter(attributes.get("Purpose", [])), None) if attr == "Personal Information Type" else None,
                        third_party_entity=predicted_values.get("Third Party Entity") if attr == "Personal Information Type" else None
                    )

    return result
