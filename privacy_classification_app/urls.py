
'''
urlpatterns = [
    path('classify/', ClassifyPolicyView.as_view(), name='classify'),
    path('classify-paragraph/', ClassifyParagraphView.as_view(), name='classify_paragraph'),
    path('classify-ui', classify_and_show, name='classify_ui'),
    path('extract-attributes/', extract_attributes_view, name='extract_attributes'),

    path('api/classify-url/', ClassifyURLView.as_view(), name='classify_url'),
    path('api/classify-paragraph/', ClassifyParagraphView.as_view(), name='classify_paragraph'),
    path('api/extract-attributes/', ExtractAttributesView.as_view(), name='extract_attributes_api'),
    path('api/summary-personal-info/', PersonalInfoSummaryView.as_view(), name='summary_personal_info'),
    path('api/collected-pit/', CollectedPersonalInfoView.as_view(), name='collected_pit'),
]
'''

from django.urls import path
from .views import ClassifyPolicyView, ClassifyParagraphView, classify_and_show, extract_attributes_view
from .views_api import ClassifyURLView, ClassifyParagraphView, ExtractAttributesView, PersonalInfoSummaryView, CollectedPersonalInfoView

urlpatterns = [
    path('classify-url/', ClassifyURLView.as_view(), name='classify_url'),
    path('classify-paragraph/', ClassifyParagraphView.as_view(), name='classify_paragraph'),
    path('extract-attributes-api/', ExtractAttributesView.as_view(), name='extract_attributes_api'),
    path('summary-personal-info/', PersonalInfoSummaryView.as_view(), name='summary_personal_info'),
    path('collected-pit/', CollectedPersonalInfoView.as_view(), name='collected_pit'),
]


