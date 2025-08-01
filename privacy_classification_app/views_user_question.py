from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import AnalyzedSentence

@method_decorator(csrf_exempt, name='dispatch')
class UserQuestionFromDBView(APIView):
    """
    输入: { "url": ..., "question_type": ... }
    输出: 根据结构化数据分析用户问题
    """
    def post(self, request):
        url = request.data.get("url")
        question_type = request.data.get("question_type")

        if not url or not question_type:
            return Response({"error": "Missing 'url' or 'question_type'"}, status=400)

        if question_type == "conflict_statement":
            return self.check_conflict(url)
        elif question_type == "third_party_sharing":
            return self.third_party_sharing(url)
        else:
            return Response({"error": "Unsupported question_type"}, status=400)

    def check_conflict(self, url):
        # 找出 First Party 中同一 attribute 既出现 "Does" 又出现 "Does Not"
        records = AnalyzedSentence.objects.filter(
            url=url,
            category="First Party Collection/Use",
            attribute="Personal Information Type"
        )

        conflict_map = {}
        for r in records:
            key = r.predicted_value
            if key:
                conflict_map.setdefault(key, set()).add(r.does_or_not_value)

        conflicts = [k for k, v in conflict_map.items() if "Does" in v and "Does Not" in v]

        return Response({
            "question": "Does this privacy policy contain any conflict statement?",
            "answer": "Yes" if conflicts else "No",
            "conflicting_attributes": conflicts
        })

    def third_party_sharing(self, url):
        records = AnalyzedSentence.objects.filter(
            url=url,
            category="Third Party Sharing/Collection",
            attribute="Personal Information Type",
            does_or_not_value="Does"
        )

        result = []
        for r in records:
            if r.predicted_value and r.third_party_entity:
                result.append({
                    "personal_info": r.predicted_value,
                    "third_party": r.third_party_entity,
                    "sentence": r.sentence
                })

        return Response({
            "question": "What personal information is shared with third parties?",
            "shared_info": result
        })

from django.shortcuts import render

from .models import AnalyzedSentence
from django.shortcuts import render

def result_view(request):
    policy_url = request.GET.get("policyUrl", "")
    question_type = request.GET.get("type", "")

    context = {
        "policy_url": policy_url,
        "question_type": question_type,
    }

    if question_type == "conflict_statement":
        # 找出有没有conflict statement
        records = AnalyzedSentence.objects.filter(
            url=policy_url,
            category="First Party Collection/Use",
            attribute="Personal Information Type"
        )

        conflict_map = {}
        for r in records:
            key = r.predicted_value
            if key:
                conflict_map.setdefault(key, set()).add(r.does_or_not_value)

        conflicts = [k for k, v in conflict_map.items() if "Does" in v and "Does Not" in v]
        context["question"] = "Does this privacy policy contain any conflict statement?"
        context["answer"] = "Yes" if conflicts else "No"
        context["conflicting_attributes"] = conflicts

    elif question_type == "third_party_sharing":
        records = AnalyzedSentence.objects.filter(
            url=policy_url,
            category="Third Party Sharing/Collection",
            attribute="Personal Information Type",
            does_or_not_value="Does"
        )

        shared_info = []
        for r in records:
            if r.predicted_value and r.third_party_entity:
                shared_info.append({
                    "personal_info": r.predicted_value,
                    "third_party": r.third_party_entity,
                    "sentence": r.sentence
                })

        context["question"] = "What personal information is shared with third parties?"
        context["shared_info"] = shared_info

    return render(request, "privacy_classification_app/result.html", context)


def form_view(request):
    return render(request, "privacy_classification_app/question_form.html")

from django.shortcuts import render

def question_form_view(request):
    url = request.GET.get("url", "")
    return render(request, "privacy_classification_app/question_form.html", {"url": url})
