# FRATERNITAS-ERP

**Sistema Integral de Administración y Tesorería para Logias Simbólicas**

---

## Descripción

FRATERNITAS-ERP es el sistema de gestión institucional desarrollado para la **Respetable Logia Simbólica Fraternidad No. 1**, perteneciente a la **Muy Respetable Gran Logia Unida Mexicana de Libres y Aceptados Masones del Gran Oriente de Veracruz**.

Su propósito es sustituir los procesos manuales basados en hojas de cálculo por una plataforma moderna, segura y orientada a procesos, permitiendo administrar:

* Miembros.
* Tesorería.
* Obligaciones económicas.
* Pagos.
* Recibos.
* Reportes financieros.
* Información administrativa.
* Estadísticas institucionales.

El sistema forma parte del ecosistema **SIGLUX (Sistema Íntegro de Gobernabilidad y Lineamientos para la User Experience)**.

---

# Filosofía del proyecto

El usuario registra **hechos**, no realiza cálculos.

FRATERNITAS-ERP interpreta automáticamente la información para:

* calcular aplicaciones de pago;
* distribuir fondos;
* generar movimientos contables;
* emitir recibos;
* mantener la trazabilidad financiera.

---

# Principios de diseño

* Simplicidad para usuarios no técnicos.
* Interfaz amigable para adultos mayores.
* Automatización de procesos repetitivos.
* Integridad de la información.
* Auditoría completa.
* Arquitectura modular.
* Escalabilidad.

---

# Arquitectura funcional

```
Hermano
      │
      ▼
Obligación
      │
      ▼
Pago
      │
      ▼
Aplicación del pago
      │
      ▼
Movimiento Contable
      │
      ▼
Recibo
```

---

# Módulos principales

## Identidad

* Configuración institucional
* Datos de la Logia
* Escudos
* Periodos administrativos

---

## Miembros

Administración del expediente completo del hermano.

Incluye:

* datos generales
* grado
* fechas de iniciación
* aumento de salario
* exaltación
* cargos
* historial

---

## Tesorería

Control de:

* ingresos
* egresos
* cuotas
* donativos
* gastos
* distribución automática de fondos

---

## Obligaciones

Generación automática de obligaciones mensuales.

Permite:

* cuotas ordinarias
* cuotas extraordinarias
* adeudos históricos
* regularizaciones

---

## Recibos

Generación de:

* recibos oficiales
* impresión
* PDF
* envío por correo
* envío por WhatsApp

---

## Reportes

Entre otros:

* Estado de Resultados
* Flujo de efectivo
* Libro diario
* Libro mayor
* Balanza
* Adeudos
* Hermanos al corriente
* Estadísticas

---

## Administración

Gestión de:

* usuarios
* roles
* permisos
* bitácoras
* respaldos

---

# Distribución automática de fondos

Cada ingreso puede distribuirse entre:

* Capitas
* Aniversario
* Saco de Beneficencia
* Taller BJ
* Otros fondos

Las reglas son configurables.

---

# Tecnologías

* Python 3.12+
* Django 5
* Bootstrap 5
* SQLite (desarrollo)
* PostgreSQL (producción)

---

# Estructura del proyecto

```
fraternitas/

├── config/
├── identidad/
├── miembros/
├── catalogos/
├── tesoreria/
├── negocio/
│   ├── domain/
│   └── services/
├── reportes/
├── templates/
├── static/
├── media/
└── docs/
```

---

# Modelo de desarrollo

Cada funcionalidad sigue el flujo:

```
Requerimiento

↓

Modelo

↓

Migración

↓

Administrador Django

↓

Pruebas

↓

Interfaz

↓

Integración

↓

Validación
```

No se considera terminada una etapa sin validación funcional.

---

# Roles del sistema

* Administrador
* Venerable Maestro
* Tesorero
* Secretario
* Consulta

Cada rol dispone de un panel específico.

---

# Seguridad

* Autenticación mediante Django Authentication.
* Control de permisos por rol.
* Registro de auditoría.
* Validaciones de integridad.
* Protección CSRF.
* Gestión segura de sesiones.

---

# Estado del proyecto

Versión actual:

**MVP en desarrollo**

Componentes implementados:

* estructura base del proyecto;
* módulos principales;
* modelos iniciales;
* panel administrativo;
* explorador de libros contables;
* importación estructural desde Excel.

Componentes en desarrollo:

* reglas de negocio;
* distribución automática;
* recibos;
* dashboard institucional;
* reportes financieros.

---

# Convenciones

## Grados

Se utilizan las abreviaturas institucionales:

* AM — Aprendiz Masón
* CM — Compañero Masón
* MM — Maestro Masón

---

# Licencia

Uso institucional exclusivo.

Todos los derechos reservados.

Respetable Logia Simbólica Fraternidad No. 1.

Gran Logia Unida Mexicana de Libres y Aceptados Masones del Gran Oriente de Veracruz.

---

# Créditos

Proyecto desarrollado dentro del ecosistema **SIGLUX**.

Sistema:

**FRATERNITAS-ERP**

Arquitectura funcional y reglas de negocio desarrolladas para la administración integral de Logias Simbólicas.
