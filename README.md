# Clínica Dental Sonrisas

Sumativa N°1 - Programación Orientada a Objeto Seguro (TI3V21), sección 114-2A-F2.
Integrantes: Francisca Garín y Fernando Miranda.

## Cómo ejecutarlo
1. Tener Python 3.9 o superior.
2. Instalar las librerías: `pip install -r requirements.txt`
3. Ejecutar: `python main.py`

Los datos se guardan solos en `datos_clinica.json` (se crea la primera vez). Para partir de cero, borra ese archivo.

## Archivos
- `main.py`: menú de consola y lectura segura de datos.
- `clinica.py`: pacientes, catálogo, fichas y guardado en JSON.
- `modelos.py`: clases del diagrama UML (herencia, clases abstractas, polimorfismo, composición).

## Reglas de negocio (cómo las interpretamos)
- **RUT:** se valida el dígito verificador (acepta `12.345.678-5`, rechaza `12.345.678-9`).
- **Cirugía:** no se agenda si la ficha del paciente tiene la alergia a la anestesia "sin registrar". Se registra en *Modificar paciente* (Sí / No).
- **Deuda:** no se atiende a un paciente con más de 60 días de deuda vencida.
- **Ortodoncia:** el costo base está en USD (brackets importados) y se multiplica por el dólar del día de `https://mindicador.cl/api/dolar`. Sin internet, el programa avisa y no calcula ese precio.
- **Ficha de atención:** una sola ficha puede tener varios tratamientos (ej. limpieza + radiografía).

## Tipos de tratamiento
| Tipo | Duración | Costo |
|---|---|---|
| Limpieza | 30 min | costo base |
| Ortodoncia | 90 min (instalación) | costo base USD × dólar del día |
| Cirugía | 120 min | costo base × 1,5 |
| Radiografía (complementaria) | 10 min | costo base |
