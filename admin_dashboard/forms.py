from django import forms
from items.models import Item


class UserStatusForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'}),
        required=True,
        max_length=500,
        help_text="Provide a clear justification for changing this account's status."
    )


class ItemModerationForm(forms.Form):
    moderation_status = forms.ChoiceField(
        choices=Item.ModerationStatus.choices,
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    is_hidden = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500 h-4 w-4'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'}),
        required=True,
        max_length=500,
        help_text="Specify the moderation justification (will be audited and emailed to user if visibility is affected)."
    )
    moderation_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'}),
        required=False,
        max_length=1000,
        help_text="Internal staff notes (never visible to user)."
    )


class AdminClaimInterventionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('APPROVE', 'Approve Claim (Mark Item Claimed)'), ('REJECT', 'Reject Claim')],
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'}),
        required=True,
        max_length=1000,
        help_text="Mandatory administrative justification for overriding or resolving this claim."
    )
