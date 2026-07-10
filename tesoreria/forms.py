from django import forms
from django.utils import timezone

from .models import Movimiento


class MovimientoIngresoForm(forms.ModelForm):

    class Meta:
        model = Movimiento

        fields = (
            "fecha",
            "recibo",
            "hermano",
            "concepto",
            "capitas",
            "aniversario",
            "saco_beneficencia",
            "taller_bj",
            "otros",
            "observaciones",
        )

        labels = {
            "taller_bj": "Taller AJEF",
            "concepto": "Concepto Contable",
            "recibo": "Número de Recibo",
            "observaciones": "Observaciones",
        }

        widgets = {
            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["fecha"].initial = timezone.localdate() 