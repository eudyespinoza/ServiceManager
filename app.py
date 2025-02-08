from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from functools import wraps
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.secret_key = '24g0iwrvp3rg3pin34pngo'

# Configurar la conexión con Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(credentials)

# Abrir las hojas de cálculo
sheet_clientes = client.open('SMMB').worksheet('CLIENTES')
sheet_direcciones = client.open('SMMB').worksheet('DIRECCIONES')
sheet_servicios = client.open('SMMB').worksheet('SERVICIOS')
sheet_usuarios = client.open('SMMB').worksheet('USUARIOS')

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_datetime(value, format='%d-%m-%Y %H:%M'):
    if value:
        try:
            datetime_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            return datetime_obj.strftime(format)
        except ValueError:
            return value
    return ''

app.jinja_env.filters['format_datetime'] = format_datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                return render_template('unauthorized.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def authenticate_user(username, password):
    try:
        cell = sheet_usuarios.find(username)
        user_row = sheet_usuarios.row_values(cell.row)
        if user_row[2] == password:
            return True, user_row[3]
        else:
            return False, None
    except gspread.exceptions.GSpreadException as e:
        print(f"Error: {e}")
        return False, None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        authenticated, role = authenticate_user(username, password)
        if authenticated:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = role
            return redirect(url_for('clientes'))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clientes')
@login_required
def clientes():
    data = sheet_clientes.get_all_records()
    return render_template('clientes.html', clientes=data)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nuevo_cliente():
    if request.method == 'POST':
        try:
            row_id = str(uuid.uuid4())
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            new_row = [row_id, None, nombre, telefono]
            sheet_clientes.append_row(new_row)
            return jsonify({"success": True, "message": "Cliente creado exitosamente"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    return render_template('nuevo_cliente.html')

@app.route('/clientes/detalle/<string:row_id>', methods=['GET'])
@login_required
def detalle_cliente(row_id):
    try:
        # Buscar el cliente por Row_ID
        cell_cliente = sheet_clientes.find(row_id)
        data_cliente = sheet_clientes.row_values(cell_cliente.row)

        # Convertir la fila del cliente en un diccionario para acceso más fácil
        headers = sheet_clientes.row_values(1)
        cliente_dict = dict(zip(headers, data_cliente))

        # Filtrar las direcciones asociadas al cliente
        direcciones = sheet_direcciones.get_all_records()
        direcciones_filtradas = [direccion for direccion in direcciones if str(direccion['ID_Cliente']) == row_id]
        print(direcciones_filtradas)

        # Filtrar los servicios asociados al cliente
        servicios = sheet_servicios.get_all_records()
        servicios_filtrados = [servicio for servicio in servicios if str(servicio['ID_Cliente']) == row_id]
        print(servicios_filtrados)

        # Renderizar el fragmento de detalles del cliente
        return render_template('detalle_cliente.html', cliente=cliente_dict, direcciones=direcciones_filtradas, servicios=servicios_filtrados)

    except Exception as e:
        return jsonify({"error": f"No se pudo cargar el detalle del cliente: {str(e)}"}), 500

@app.route('/clientes/editar/<string:id_cliente>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_cliente(id_cliente):
    try:
        cell = sheet_clientes.find(id_cliente)
        if request.method == 'POST':
            # Actualización del cliente
            nombre = request.form['nombre']
            condicion = request.form.get('condicion') == 'True'
            telefono = request.form['telefono']
            sheet_clientes.update_cell(cell.row, 2, nombre)
            sheet_clientes.update_cell(cell.row, 3, condicion)
            sheet_clientes.update_cell(cell.row, 4, telefono)
            return jsonify({"success": True, "message": "Cliente actualizado exitosamente"})

        # Carga del formulario
        cliente = sheet_clientes.row_values(cell.row)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('editar_cliente.html', cliente=cliente)

        return render_template('editar_cliente.html', cliente=cliente)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/clientes/borrar/<string:id_cliente>', methods=['POST'])
@login_required
@role_required('admin')
def borrar_cliente(id_cliente):
    try:
        cell = sheet_clientes.find(id_cliente)
        sheet_clientes.delete_rows(cell.row)
        return jsonify({"success": True, "message": "Cliente eliminado exitosamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/direcciones/nueva/<string:id_cliente>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nueva_direccion(id_cliente):
    if request.method == 'POST':
        try:
            row_id = str(uuid.uuid4())
            direccion = request.form['direccion']
            new_row = [id_cliente, direccion, row_id]
            sheet_direcciones.append_row(new_row)
            return jsonify({"success": True, "message": "Dirección agregada exitosamente"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    return render_template('nueva_direccion.html', id_cliente=id_cliente)

@app.route('/direcciones/detalle/<string:id_direccion>', methods=['GET'])
@login_required
def detalle_direccion(id_direccion):
    try:
        print(f"📌 Buscando dirección con ID: {id_direccion}")

        # Obtener los encabezados de la hoja para saber en qué columna está "🔒 Row ID"
        headers = sheet_direcciones.row_values(1)

        # Buscar la posición de la columna "🔒 Row ID"
        try:
            col_index = headers.index("🔒 Row ID") + 1  # Convertimos a índice de Google Sheets (1-based)
        except ValueError:
            print("❌ No se encontró la columna '🔒 Row ID' en la hoja.")
            return jsonify({"error": "Error interno: Columna '🔒 Row ID' no encontrada"}), 500

        # Obtener SOLO los valores de la columna "🔒 Row ID"
        row_ids = sheet_direcciones.col_values(col_index)

        # Buscar el índice de la fila que tiene el ID
        try:
            row_index = row_ids.index(id_direccion) + 1  # Convertimos a índice de Google Sheets (1-based)
        except ValueError:
            print("❌ Dirección no encontrada en la columna '🔒 Row ID'.")
            return jsonify({"error": "Dirección no encontrada"}), 404

        # Obtener los valores de la fila donde está la dirección
        direccion = sheet_direcciones.row_values(row_index)

        # Convertir la fila en un diccionario
        direccion_dict = dict(zip(headers, direccion))
        print(direccion_dict)
        # Renderizar la plantilla con la información de la dirección
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('detalle_direccion.html', direccion=direccion_dict)

        return redirect(url_for('clientes'))

    except Exception as e:
        print(f"❌ Error en detalle_direccion: {str(e)}")
        return jsonify({"error": f"No se pudo cargar el detalle de la dirección: {str(e)}"}), 500


@app.route('/direcciones/editar/<string:id_direccion>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_direccion(id_direccion):
    try:
        cell = sheet_direcciones.find(id_direccion)
        if request.method == 'POST':
            direccion = request.form['direccion']
            sheet_direcciones.update_cell(cell.row, 2, direccion)
            return jsonify({"success": True, "message": "Dirección actualizada exitosamente"})
        direccion = sheet_direcciones.row_values(cell.row)
        return render_template('editar_direccion.html', direccion=direccion)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/direcciones/borrar/<string:id_direccion>', methods=['POST'])
@login_required
@role_required('admin')
def borrar_direccion(id_direccion):
    try:
        cell = sheet_direcciones.find(id_direccion)
        sheet_direcciones.delete_row(cell.row)
        return jsonify({"success": True, "message": "Dirección eliminada exitosamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/servicios/nuevo/<string:id_cliente>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def nuevo_servicio(id_cliente):
    if request.method == 'POST':
        try:
            row_id = str(uuid.uuid4())
            direccion = request.form['direccion']
            servicio = request.form['servicio']
            notas = request.form.get('notas', '')
            fecha_hora = request.form['fecha_hora']
            fecha_hora_obj = datetime.strptime(fecha_hora, '%Y-%m-%d %H:%M')
            fecha_hora_str = fecha_hora_obj.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            new_row = [id_cliente, direccion, servicio, notas, fecha_hora_str, row_id]
            sheet_servicios.append_row(new_row)
            return jsonify({"success": True, "message": "Servicio agregado exitosamente"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    direcciones = sheet_direcciones.get_all_records()
    direcciones_filtradas = [d for d in direcciones if str(d['ID_Cliente']) == id_cliente]
    return render_template('nuevo_servicio.html', id_cliente=id_cliente, direcciones=direcciones_filtradas)

@app.route('/servicios/detalle/<string:id_servicio>', methods=['GET'])
@login_required
def detalle_servicio(id_servicio):
    try:
        cell = sheet_servicios.find(id_servicio)
        if not cell:
            return jsonify({"error": "Servicio no encontrado"}), 404

        servicio_data = sheet_servicios.row_values(cell.row)
        headers = sheet_servicios.row_values(1)
        servicio = dict(zip(headers, servicio_data))
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render_template('detalle_servicio.html', servicio=servicio)

        return redirect(url_for('clientes'))
    except Exception as e:
        print(f"❌ Error en detalle_servicio: {str(e)}")  # 👈 Log para errores
        return jsonify({"error": f"No se pudo cargar el detalle del servicio: {str(e)}"}), 500

@app.route('/servicios/editar/<string:id_servicio>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_servicio(id_servicio):
    try:
        cell = sheet_servicios.find(id_servicio)
        if request.method == 'POST':
            direccion = request.form['direccion']
            servicio = request.form['servicio']
            notas = request.form.get('notas', '')
            sheet_servicios.update_cell(cell.row, 2, direccion)
            sheet_servicios.update_cell(cell.row, 3, servicio)
            sheet_servicios.update_cell(cell.row, 4, notas)
            return jsonify({"success": True, "message": "Servicio actualizado exitosamente"})
        servicio = sheet_servicios.row_values(cell.row)
        return render_template('editar_servicio.html', servicio=servicio)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/servicios/borrar/<string:id_servicio>', methods=['POST'])
@login_required
@role_required('admin')
def borrar_servicio(id_servicio):
    try:
        cell = sheet_servicios.find(id_servicio)
        sheet_servicios.delete_row(cell.row)
        return jsonify({"success": True, "message": "Servicio eliminado exitosamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/agenda')
@login_required
def agenda():
    try:
        return render_template('agenda.html')
    except Exception as e:
        return render_template('error.html', error=e)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    #app.run(debug=True)
