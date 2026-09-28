import os
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from PIL import Image

from .models import Item


class ItemForm(forms.ModelForm):
    """
    Unified form for reporting Lost and Found items.
    Supports both Report Lost and Report Found flows.
    Excludes user, status, and timestamps from user editing.
    """

    # Optional item_type hidden field or constructor arg for unified flow
    item_type = forms.ChoiceField(
        choices=Item.ItemType.choices,
        required=False,
        widget=forms.HiddenInput()
    )

    title = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'item-name',
            'placeholder': 'e.g. Matte Black Commuter Backpack with 15-inch Sleeve',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please enter a title for the item report.',
        }
    )

    category = forms.ChoiceField(
        choices=[('', 'Select category')] + list(Item.ItemCategory.choices),
        required=True,
        widget=forms.Select(attrs={
            'id': 'item-category',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please select a category.',
            'invalid_choice': 'Please select a valid category from the list.',
        }
    )

    brand = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'item-brand',
            'placeholder': 'e.g. Apple, Wildcraft, Samsonite',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        })
    )

    color = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'item-color',
            'placeholder': 'e.g. Matte Black, Navy Blue, Silver',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        })
    )

    description = forms.CharField(
        max_length=2000,
        required=True,
        widget=forms.Textarea(attrs={
            'id': 'item-description',
            'rows': 4,
            'placeholder': 'Describe appearance, materials, compartments, stickers, and distinguishing qualities...',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please provide a detailed description of the item.',
        }
    )

    location = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'lost-location',
            'placeholder': 'e.g. Central Metro Station, Line 2 Platform 3',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please enter the location where the item was lost or found.',
        }
    )

    date_occurred = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'id': 'lost-date',
            'type': 'date',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please enter the date the incident occurred.',
            'invalid': 'Please enter a valid date in YYYY-MM-DD format.',
        }
    )

    time_occurred = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'id': 'lost-time',
            'type': 'time',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        })
    )

    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'id': 'file-input',
            'accept': 'image/jpeg,image/png,image/webp',
            'class': 'hidden',
        }),
        error_messages={
            'invalid_image': 'Please upload a valid image file.',
            'invalid': 'Please upload a valid image file.',
        }
    )

    identification_details = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'private-marks',
            'rows': 3,
            'placeholder': 'Add details that only the rightful owner would know (e.g. scratch near logo, serial ending in 4123, unique sticker inside pocket)...',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        })
    )

    class Meta:
        model = Item
        fields = [
            'title',
            'description',
            'category',
            'brand',
            'color',
            'location',
            'date_occurred',
            'time_occurred',
            'image',
            'identification_details',
        ]

    def __init__(self, *args, item_type=None, **kwargs):
        """
        Support passing item_type directly (e.g. Item.ItemType.LOST or Item.ItemType.FOUND)
        to pre-configure or enforce item type during view handling.
        """
        self.preset_item_type = item_type
        super().__init__(*args, **kwargs)
        if self.preset_item_type:
            self.fields['item_type'].initial = self.preset_item_type

    def clean_date_occurred(self):
        date = self.cleaned_data.get('date_occurred')
        if date and date > timezone.now().date():
            raise ValidationError('The lost/found date cannot be in the future.')
        return date

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image or not hasattr(image, 'file'):
            return image

        if isinstance(image, UploadedFile):
            # Check maximum file size (10MB limit)
            max_size = 10 * 1024 * 1024
            if image.size > max_size:
                raise ValidationError("Please upload a valid image file. Size must be under 10MB.")

            # Validate file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("Please upload a valid image file (JPG, PNG, or WebP).")

            # Validate image binary content with Pillow
            try:
                img = Image.open(image)
                img.verify()
                if img.format.lower() not in ['jpeg', 'png', 'webp']:
                    raise ValidationError("Please upload a valid image file.")
                if hasattr(image, 'seek'):
                    image.seek(0)
            except Exception:
                raise ValidationError("Please upload a valid image file.")

        return image

    def save(self, commit=True):
        item = super().save(commit=False)
        item_type = self.cleaned_data.get('item_type') or self.preset_item_type
        if item_type and not item.item_type:
            item.item_type = item_type
        if commit:
            item.save()
            self.save_m2m()
        return item
