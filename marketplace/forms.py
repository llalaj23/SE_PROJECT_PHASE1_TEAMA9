from django import forms
from django.core.exceptions import ValidationError
from .models import Item, ItemImage, Review, Report

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGES = 8

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['itemName', 'itemPrice', 'categoryID', 'condition', 'description', 'city']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'itemName': forms.TextInput(attrs={'placeholder': 'What are you selling?'}),
            'itemPrice': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Tiranë'}),
        }
        labels = {
            'itemName': 'Title',
            'itemPrice': 'Price (Lek)',
            'categoryID': 'Category',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].required = True


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Rating',
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Share your experience with this seller…',
            }),
        }
        labels = {
            'comment': 'Comment (optional)',
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'reportDescription', 'screenshot']
        widgets = {
            'reason': forms.RadioSelect,
            'reportDescription': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe what happened (optional)…',
            }),
        }
        labels = {
            'reason': 'Reason',
            'reportDescription': 'Additional details (optional)',
            'screenshot': 'Screenshot (optional)',
        }
