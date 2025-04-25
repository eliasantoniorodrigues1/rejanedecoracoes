from django import forms
from .models import Lead
from django.core.exceptions import ValidationError

from django.conf import settings
from PIL import Image
from io import BytesIO


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['nome', 'email', 'mensagem']

