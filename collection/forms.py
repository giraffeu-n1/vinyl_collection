from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Album, WishlistItem


class AlbumMetadataForm(forms.ModelForm):
    """Основные поля альбома без обложки (фото управляются отдельно)."""

    class Meta:
        model = Album
        fields = ('artist', 'title', 'description')
        widgets = {
            'artist': forms.TextInput(attrs={'placeholder': 'Например: Pink Floyd'}),
            'title': forms.TextInput(attrs={'placeholder': 'Например: The Dark Side of the Moon'}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Год, лейбл, заметки о пластинке…',
            }),
        }
        labels = {
            'artist': 'Группа / исполнитель',
            'title': 'Название альбома',
            'description': 'Описание',
        }


AlbumCreateForm = AlbumMetadataForm
AlbumEditForm = AlbumMetadataForm
AlbumForm = AlbumMetadataForm


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Имя пользователя'})
        self.fields['email'].widget.attrs.update({'placeholder': 'email@example.com'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class WishlistForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ('artist', 'title', 'photo', 'note')
        widgets = {
            'artist': forms.TextInput(attrs={'placeholder': 'Назример: Pink Floyd'}),
            'title': forms.TextInput(attrs={'placeholder': 'Например: Wish You Were Here'}),
            'note': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Год, лейбл, где искать…',
            }),
        }
        labels = {
            'artist': 'Группа',
            'title': 'Альбом',
            'photo': 'Фото',
            'note': 'Примечание',
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'placeholder': 'Группа или название альбома…',
            'autocomplete': 'off',
        }),
    )
