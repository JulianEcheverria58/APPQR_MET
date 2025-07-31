from flask import Flask, render_template, request, redirect, url_for, Response
from functools import wraps
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import os

app = Flask(__name__)

# Configuración PWA y subida de archivos
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

# Autenticación básica para admin
def check_auth(username, password):
    return username == "admin" and password == "tucontraseña"

def authenticate():
    return Response(
        'Acceso requerido', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Función para generar gráfico
def crear_grafico_horas(df, maquina_id):
    try:
        df_maquina = df[df['id_equipo'] == maquina_id].copy()
        df_maquina['Fecha'] = pd.to_datetime(df_maquina['Fecha'], dayfirst=True)
        
        df_mensual = df_maquina.groupby(df_maquina['Fecha'].dt.to_period('M'))['HORAS'].sum().reset_index()
        df_mensual['Mes'] = df_mensual['Fecha'].dt.strftime('%b-%Y')
        df_mensual = df_mensual.sort_values('Fecha')
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df_mensual['Mes'], df_mensual['HORAS'], color='#3498db')
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'{int(height)}h',
                     ha='center', va='bottom')
        
        plt.title(f'Horas trabajadas por mes - {maquina_id}')
        plt.xlabel('Mes')
        plt.ylabel('Horas trabajadas')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=80)
        buffer.seek(0)
        plt.close()
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error generando gráfico: {str(e)}")
        return None

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para información de máquina
@app.route('/maquina/<maquina_id>')
def maquina_detail(maquina_id):
    try:
        df = pd.read_excel('maquinaria.xlsx', sheet_name='Hoja3')
        df_maquina = df[df['id_equipo'] == maquina_id].sort_values('Fecha', ascending=False)
        
        if df_maquina.empty:
            return render_template('error.html', mensaje=f"Máquina {maquina_id} no encontrada")
            
        ultimo_registro = df_maquina.iloc[0].to_dict()
        grafico = crear_grafico_horas(df, maquina_id)
        
        return render_template('maquina.html', 
                            maquina={
                                'id': maquina_id,
                                'nombre': ultimo_registro['Equipo'],
                                'modelo': ultimo_registro['Linea'],
                                'fecha_ultimo_registro': ultimo_registro['Fecha'].strftime('%d/%m/%Y') if isinstance(ultimo_registro['Fecha'], datetime) else ultimo_registro['Fecha'],
                                'horas_totales': df_maquina['HORAS'].sum(),
                                'ultimo_operador': ultimo_registro['Operador'],
                                'ultima_observacion': ultimo_registro['UltimaObservacion'],
                                'proyecto': ultimo_registro['Det_ProyectoNombre'],
                                'odometro': ultimo_registro['ODOMETRO'],
                                'grafico_horas': grafico
                            })
    except Exception as e:
        return render_template('error.html', mensaje=f"Error: {str(e)}")

# Ruta para subir archivo Excel
@app.route('/admin')
@requires_auth
def admin():
    return '''
    <!doctype html>
    <title>Panel de Administración</title>
    <h1>Actualizar Base de Datos</h1>
    <form method=post enctype=multipart/form-data action="/upload">
      <input type=file name=file accept=".xlsx">
      <input type=submit value=Actualizar>
    </form>
    '''

@app.route('/upload', methods=['POST'])
@requires_auth
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('admin'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('admin'))
    if file and file.filename.endswith('.xlsx'):
        file.save('maquinaria.xlsx')
        return redirect(url_for('index'))
    return redirect(url_for('admin'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)