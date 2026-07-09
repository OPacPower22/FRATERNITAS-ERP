from django import forms

from .models import Movimiento


class MovimientoIngresoForm(forms.ModelForm):

    class Meta:
        model = Movimiento

        fields = (
            "fecha",
            "recibo",
            "hermano",
            "concepto",
            "descripcion",
            "capitas",
            "aniversario",
            "saco_beneficencia",
            "taller_bj",
            "otros",
            "justificacion",
        )
