from django import forms
from .models import Claim


class ClaimForm(forms.ModelForm):
    """
    Form for claiming ownership of a FOUND item.
    Only exposes reason and verification_answer.
    All other fields (item, claimant, status, reviewer, timestamps) are strictly server-controlled.
    """

    reason = forms.CharField(
        label="Why do you believe this item belongs to you?",
        max_length=2000,
        required=True,
        widget=forms.Textarea(attrs={
            'id': 'claim-reason',
            'rows': 4,
            'placeholder': 'Explain why you believe this item is yours (e.g. where/when you lost it, distinctive traits, circumstances)...',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        error_messages={
            'required': 'Please provide a reason explaining why this item belongs to you.',
        },
        help_text='Provide a meaningful explanation of your ownership claim.'
    )

    verification_answer = forms.CharField(
        label="Verification Information",
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'claim-verification-answer',
            'rows': 4,
            'placeholder': 'Provide information that can help the reporter verify ownership (e.g. hidden markings, screen appearance, specific contents)...',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        }),
        help_text='Do not share passwords, financial information, or unnecessary sensitive personal information.'
    )

    class Meta:
        model = Claim
        fields = ['reason', 'verification_answer']

    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()
        if not reason:
            raise forms.ValidationError('Please provide a meaningful reason for your claim.')
        if len(reason) < 10:
            raise forms.ValidationError('Please provide a more detailed reason (at least 10 characters).')
        return reason


class RejectClaimForm(forms.Form):
    """
    Form for rejecting a claim with an optional reviewer note.
    """
    reviewer_note = forms.CharField(
        label="Reason for Rejection",
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'reviewer-note',
            'rows': 3,
            'placeholder': 'Provide a brief explanation for why this claim was not accepted (optional)...',
            'class': 'w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-xs sm:text-sm text-navy placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all',
        })
    )
