from django import forms

from .models import Hermano


class HermanoForm(forms.ModelForm):

    class Meta:
        model = Hermano

        fields = [
            "numero_control",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "nombre_simbolico",
            "fotografia",
            "fecha_nacimiento",
            "lugar_nacimiento",
            "profesion",
            "ocupacion",
            "telefono",
            "celular",
            "correo",
            "direccion",
            "grado",
            "tipo_ingreso",
            "fecha_ingreso",
            "fecha_iniciacion",
            "fecha_aumento",
            "fecha_exaltacion",
            "logia_procedencia",
            "estatus",
            "observaciones",
        ]

        widgets = {
            "numero_control": forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_paterno": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_materno": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_simbolico": forms.TextInput(attrs={"class": "form-control"}),
            "fotografia": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "lugar_nacimiento": forms.TextInput(attrs={"class": "form-control"}),
            "profesion": forms.TextInput(attrs={"class": "form-control"}),
            "ocupacion": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "celular": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "grado": forms.Select(attrs={"class": "form-select"}),
            "tipo_ingreso": forms.Select(attrs={"class": "form-select"}),
            "fecha_ingreso": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_iniciacion": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_aumento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "fecha_exaltacion": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "logia_procedencia": forms.TextInput(attrs={"class": "form-control"}),
            "estatus": forms.Select(attrs={"class": "form-select"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
