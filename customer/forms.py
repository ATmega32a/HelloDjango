from django import forms


class UserForm(forms.Form):
    search = forms.CharField(max_length=255, label="Поиск",
                             help_text="Введите поисковые слова",
                             required=False, error_messages={'required': 'Вы не ввели слова для поиска'}, )

