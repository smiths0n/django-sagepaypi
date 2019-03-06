from django import forms


class Complete3DSecureForm(forms.Form):
    PaRes = forms.CharField()

    def __init__(self, transaction, *args, **kwargs):
        self.transaction = transaction
        super().__init__(*args, **kwargs)

    def save(self):
        return self.transaction.get_3d_secure_status(self.cleaned_data['PaRes'])
