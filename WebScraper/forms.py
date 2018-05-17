from django import forms


class UrlsForm(forms.Form):
    urls = forms.CharField(widget=forms.Textarea, label="urls", required=True)
