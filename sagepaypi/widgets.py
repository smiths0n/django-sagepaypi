from django import forms


class ExpiryDateWidget(forms.widgets.MultiWidget):
    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]
