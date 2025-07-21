
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
from .views_api import FilterSentencesByPITView
from .views import test_filter_sentences_page

from .views_api_cached import ExtractAttributesCachedView, CollectedAndSharedDetailedView
from privacy_classification_app.views import index

urlpatterns = [
    path('classify-url/', ClassifyURLView.as_view(), name='classify_url'),
    path('classify-paragraph/', ClassifyParagraphView.as_view(), name='classify_paragraph'),
    path('extract-attributes-api/', ExtractAttributesView.as_view(), name='extract_attributes_api'),
    path('summary-personal-info/', PersonalInfoSummaryView.as_view(), name='summary_personal_info'),
    path('collected-pit/', CollectedPersonalInfoView.as_view(), name='collected_pit'),
    path('filter-sentences-by-pit/', FilterSentencesByPITView.as_view(), name='filter-sentences-by-pit'),
    path('test/filter-sentences/', test_filter_sentences_page, name='test_filter_sentences_page'),

    path("extract-attributes-cached/", ExtractAttributesCachedView.as_view(), name="extract_attributes_cached"),
    path('collected-and-shared-detailed/', CollectedAndSharedDetailedView.as_view(), name='collected_and_shared_detailed'),

    path('', index, name='index'),
]


