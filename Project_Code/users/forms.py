from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'bio', 'city', 'phoneNumber', 'gender', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell people a bit about yourself…'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Tiranë'}),
            'phoneNumber': forms.TextInput(attrs={'placeholder': 'e.g. +355 69 123 4567'}),
            'gender': forms.Select(choices=[
                ('', '— Select —'),
                ('Male', 'Male'),
                ('Female', 'Female'),
                ('Other', 'Other'),
            ]),
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }
        labels = {
            'full_name': 'Full Name',
            'bio': 'Bio',
            'city': 'City',
            'phoneNumber': 'Phone Number',
            'gender': 'Gender',
            'profile_picture': 'Profile Picture',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nothing is mandatory — only update fields the user fills in
        for field in self.fields.values():
            field.required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        # For every text/choice field left blank, restore the existing value
        text_fields = ['full_name', 'bio', 'city', 'phoneNumber', 'gender']
        for field_name in text_fields:
            if not self.cleaned_data.get(field_name):
                setattr(user, field_name, getattr(self.instance, field_name))
        # If no new picture was uploaded, keep the existing one
        if not self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.instance.profile_picture
        if commit:
            user.save()
        return user
