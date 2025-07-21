from ..views_api import extract_paragraphs_from_url, predict_paragraph_category
from ..views_api import extract_from_paragraph, span_model, span_tokenizer
from ..attribute_predictor import predict_purpose_value, predict_does_not_label, predict_pit_value
from ..utils import is_real_span

def run_privacy_pipeline(url):
    """
    执行完整的隐私策略分析，返回带详细信息的 JSON。
    """
    paragraphs = extract_paragraphs_from_url(url)
    first_party_map = {}
    third_party_map = {}

    for para in paragraphs:
        labels = predict_paragraph_category(para)
        if not any(lbl in ["First Party Collection/Use", "Third Party Sharing/Collection"] for lbl in labels):
            continue

        extracted = extract_from_paragraph(para, labels, span_model, span_tokenizer)
        for sentence_item in extracted:
            category = sentence_item.get("category")
            attributes = sentence_item.get("attributes", {})
            sentence = sentence_item.get("sentence", "")

            does_spans = attributes.get("Does/Does Not", [])
            does_text_span = does_spans[0] if does_spans else None
            does_value = predict_does_not_label(", ".join(does_spans)) if does_spans else "Unknown"

            purpose_spans = attributes.get("Purpose", [])
            purpose_text_span = purpose_spans[0] if purpose_spans else None
            purpose_value = predict_purpose_value(purpose_text_span) if purpose_text_span else "Unknown"

            for pit_span in attributes.get("Personal Information Type", []):
                if is_real_span(pit_span, sentence):
                    predicted_value = predict_pit_value(pit_span)
                    detail_tuple = (
                        pit_span, sentence, does_value, does_text_span, purpose_value, purpose_text_span
                    )

                    if category == "First Party Collection/Use" and does_value == "Does":
                        first_party_map.setdefault(predicted_value, set()).add(detail_tuple)
                    elif category == "Third Party Sharing/Collection"and does_value == "Does":
                        third_party_map.setdefault(predicted_value, set()).add(detail_tuple)

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

    return {
        "url": url,
        "first_party_collected": format_details(first_party_map),
        "third_party_shared": format_details(third_party_map)
    }
