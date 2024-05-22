from django.contrib import admin
from botviber.models import ConditionsForRegions
#, WaybillQuestionnaireButtons, \
#    QuestionnaireButtons, Button, Questions, LicensingQuestionnaireButtons, CarQuestionnaireButtons, CarCreateQuestions

#admin.site.register(LicensingQuestionnaireButtons)
#admin.site.register(CarQuestionnaireButtons)
#admin.site.register(CarCreateQuestions)


#@admin.register(Questions)
#class ViewQuestions(admin.ModelAdmin):
#    list_display = (
#        'questions',
#    )


#@admin.register(Button)
#class ViewButton(admin.ModelAdmin):
#    list_display = (
#        'button_id',
#        'bg_color',
#        'action_type',
#        'action_body'
#    )


#@admin.register(QuestionnaireButtons)
#class ViewQButtons(admin.ModelAdmin):
#    list_display = (
#        'user',
#        'get_buttons',
#    )


#@admin.register(WaybillQuestionnaireButtons)
#class ViewWaybillQuestionnaireButtons(admin.ModelAdmin):
#    list_display = (
#        'user',
#        'edit',
#        'get_buttons',
#    )


@admin.register(ConditionsForRegions)
class ViewConditionsForRegions(admin.ModelAdmin):
    list_display = (
        'region_name',
        'condition'
    )
