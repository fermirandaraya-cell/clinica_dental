from flask import Flask, render_template, request, redirect, url_for, flash
from clinica import Clinica
import math

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_mensajes'
clinica = Clinica("datos_clinica.json")

# Filtro para formatear pesos
@app.template_filter('clp')
def clp_filter(monto):
    if not math.isfinite(monto): return "N/A"
    return f"${int(monto):,}".replace(",", ".")

@app.route('/')
def index():
    return render_template('index.html', clinica=clinica)

@app.route('/pacientes')
def listar_pacientes():
    return render_template('pacientes.html', pacientes=clinica.pacientes.values())

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        rut = request.form.get('rut')
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono', '')
        correo = request.form.get('correo', '')
        try:
            clinica.registrar_paciente(rut, nombre, telefono, correo)
            flash("¡Paciente registrado exitosamente!", "success")
            return redirect(url_for('listar_pacientes'))
        except ValueError as e:
            flash(f"Error al registrar: {e}", "danger")
    return render_template('registrar.html')

@app.route('/paciente/<rut>', methods=['GET', 'POST'])
def perfil_paciente(rut):
    paciente = clinica.buscar_paciente(rut)
    if not paciente:
        flash("Paciente no encontrado", "danger")
        return redirect(url_for('listar_pacientes'))
        
    if request.method == 'POST':
        try:
            clinica.modificar_paciente(rut, "telefono", request.form.get('telefono'))
            clinica.modificar_paciente(rut, "correo", request.form.get('correo'))
            clinica.modificar_paciente(rut, "alergias", request.form.get('alergias'))
            clinica.modificar_paciente(rut, "dias_deuda_vencida", int(request.form.get('deuda', 0)))
            
            anestesia = request.form.get('anestesia')
            anestesia_val = True if anestesia == 'si' else False if anestesia == 'no' else None
            clinica.modificar_paciente(rut, "alergia_anestesia", anestesia_val)
            
            nuevo_historial = request.form.get('nuevo_historial')
            if nuevo_historial:
                paciente.actualizar_historial(nuevo_historial)
                clinica.guardar()
                
            flash("Datos actualizados correctamente", "success")
        except ValueError as e:
            flash(f"Error al actualizar: {e}", "danger")
            
    return render_template('perfil_paciente.html', p=paciente)

@app.route('/catalogo')
def catalogo():
    clinica.refrescar_dolar()
    return render_template('catalogo.html', tratamientos=clinica.tratamientos.values(), indicador=clinica.indicador)

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        rut = request.form.get('rut')
        hora = request.form.get('hora')
        tratamientos_ids = request.form.getlist('tratamientos')
        
        try:
            paciente = clinica.buscar_paciente(rut)
            if not paciente: raise ValueError("Paciente no encontrado.")
            
            items = []
            for tid in tratamientos_ids:
                trat = clinica.tratamientos.get(int(tid))
                if trat:
                    items.append((trat, 1))
                    
            if not items:
                raise ValueError("Debe seleccionar al menos un tratamiento.")
            
            ok, motivo, atencion = clinica.registrar_atencion(
                paciente=paciente,
                hora=hora,
                items=items,
                pabellon_disponible=True
            )
            
            if not ok:
                flash(f"No se pudo agendar: {motivo}", "danger")
            else:
                flash("¡Hora agendada exitosamente!", "success")
                return redirect(url_for('atenciones'))
        except Exception as e:
            flash(f"Error al agendar: {e}", "danger")

    return render_template('agendar.html', pacientes=clinica.pacientes.values(), tratamientos=clinica.tratamientos.values())

@app.route('/atenciones')
def atenciones():
    return render_template('atenciones.html', atenciones=clinica.atenciones)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
