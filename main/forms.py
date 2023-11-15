from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Questionnaire, EvalSched, InstructorQuestionnaire, Subjects
from django.forms.widgets import DateInput
from django.core.exceptions import ValidationError
import datetime

User = get_user_model()

class UpdateUserForm(forms.ModelForm):
  email = forms.EmailField(disabled=True)
  class Meta:
    model = User
    fields = ["email", "first_name", "last_name", "image"]

class UpdateQuestionnaire(forms.ModelForm):
  category = forms.CharField(disabled=True)
  question = forms.CharField(widget=forms.Textarea(attrs={"rows":5}), required=True)

  class Meta:
    model = Questionnaire
    fields = ["category", "question"]

class UpdateInstructorQuestionnaire(forms.ModelForm):
  category = forms.CharField(disabled=True)
  question = forms.CharField(widget=forms.Textarea(attrs={"rows":5}), required=True)

  class Meta:
    model = InstructorQuestionnaire
    fields = ["category", "question"]

class BulkReg(forms.Form):
  file = forms.FileField()

class EvalSchedForm(forms.ModelForm):
  class Meta:
    model = EvalSched
    fields = ["date_from", "date_to"]
    widgets = {
      'date_from': DateInput(attrs={'type': 'date'}),
      'date_to': DateInput(attrs={'type': 'date'}),
    }
  def clean(self):
    cleaned_data = super().clean()
    date_from = cleaned_data.get("date_from")
    date_to = cleaned_data.get("date_to")

    if date_from and date_to:
      # Only do something if both fields are valid so far.
      if date_from < datetime.date.today():
        raise ValidationError(
          "Starting date is past today's date."
      )
      if date_to < date_from:
        raise ValidationError(
          "End date is past starting date."
      )

class EvalSchedFormOngoing(forms.ModelForm):
  date_from = forms.DateField(disabled=True)
  class Meta:
    model = EvalSched
    fields = ["date_from", "date_to"]
    widgets = {
      'date_from': DateInput(attrs={'type': 'date'}),
      'date_to': DateInput(attrs={'type': 'date'}),
    }
  def clean(self):
    cleaned_data = super().clean()
    date_from = cleaned_data.get("date_from")
    date_to = cleaned_data.get("date_to")

    if date_from and date_to:
      # Only do something if both fields are valid so far.
      if date_to < datetime.date.today() or date_to < date_from:
        raise ValidationError(
          "End date is past today's date."
      )

class UpdateSubjects(forms.ModelForm):
  class Meta:
    model = Subjects
    fields = ["description", "code"]