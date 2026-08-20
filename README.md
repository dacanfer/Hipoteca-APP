# Optimizador Hipotecario

Aplicacion en Python y Streamlit para comparar hipotecas, optimizar productos vinculados y analizar la amortizacion anticipada y la venta futura de una vivienda.

## Funcionalidades

### Optimizador Hipotecario

La pagina principal permite:

- Introducir el precio del inmueble.
- Elegir el porcentaje del precio que se desea financiar.
- Calcular automaticamente el capital hipotecario.
- Introducir los impuestos como porcentaje del precio y ver su importe en euros.
- Introducir los gastos previstos de la hipoteca.
- Comprobar si los ahorros disponibles cubren la entrada, impuestos y gastos.
- Configurar productos vinculados con:
  - Nombre.
  - Bonificacion sobre el tipo de interes.
  - Coste mensual con el banco.
  - Coste mensual externo.
  - Indicador de producto obligatorio.
- Generar las combinaciones posibles de productos:
  - `No`: no contratado.
  - `Banco`: contratado con el banco.
  - `Externo`: contratado fuera del banco.
- Excluir automaticamente la opcion `No` para los productos marcados como obligatorios.
- Ordenar los resultados por coste mensual total.
- Mostrar el escenario optimo en formato tabla.
- Consultar KPI del mejor escenario.
- Comparar los diez escenarios mas baratos mediante un grafico.
- Cambiar el desglose del grafico entre hipoteca/productos y coste individual de cada producto.
- Exportar los resultados a Excel.
- Guardar y cargar configuraciones en JSON.

Por defecto, los productos Nómina y Hogar aparecen marcados como obligatorios. El usuario puede desmarcarlos si las condiciones del banco son diferentes.

### Amortizacion Hipotecaria

La pagina `Amortizacion Hipotecaria` reutiliza los datos de la pagina principal mediante `st.session_state` cuando estan disponibles y permite:

- Generar un cuadro de amortizacion mensual con sistema frances.
- Introducir una aportacion mensual extra.
- Elegir el mes a partir del cual empieza la aportacion extra.
- Comparar hipoteca normal frente a hipoteca con amortizacion anticipada.
- Consultar cuota, intereses, capital amortizado, capital pendiente y fecha estimada mes a mes.
- Ver los meses ahorrados e intereses ahorrados.
- Visualizar capital pendiente, intereses acumulados y patrimonio neto.
- Simular una venta futura usando un mes concreto.
- Comparar capital pendiente, intereses pagados, capital amortizado y dinero neto recibido en ambos escenarios.
- Introducir comision de cancelacion, gastos de agencia, gastos legales y otros costes.
- Exportar los cuadros mensuales a Excel.

## Estructura del proyecto

```text
Hipotecas/
├── Optimizador_Hipotecario.py
├── amortization.py
├── mortgage.py
├── optimizer.py
├── utils.py
├── requirements.txt
├── README.md
└── pages/
    └── 1_🏦_Amortización_Hipotecaria.py
```

### Responsabilidad de cada modulo

- `Optimizador_Hipotecario.py`: pagina principal de Streamlit y formulario del optimizador.
- `optimizer.py`: genera escenarios y calcula el coste de cada combinacion.
- `mortgage.py`: calcula cuotas y costes de la hipoteca.
- `amortization.py`: contiene los calculos mensuales de amortizacion y venta futura.
- `utils.py`: configuraciones JSON y exportacion a Excel.
- `pages/1_🏦_Amortización_Hipotecaria.py`: interfaz de la pagina de amortizacion.

## Requisitos

- Python 3.10 o superior.
- `pip`.
- Navegador web.

Las dependencias del proyecto estan en `requirements.txt`.

## Instalacion

Abre PowerShell y situa la terminal en la carpeta del proyecto:

```powershell
cd "c:\ruta\a\Hipotecas"
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

En Windows, si `python` no apunta al interprete correcto, puedes utilizar:

```powershell
py -m pip install -r requirements.txt
```

### Entorno virtual recomendado

Para evitar mezclar las dependencias con otros proyectos:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno virtual, ejecuta PowerShell como usuario y utiliza directamente el interprete del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecucion

Desde la carpeta `Hipotecas`, ejecuta:

```powershell
streamlit run Optimizador_Hipotecario.py
```

Streamlit mostrara una URL parecida a:

```text
http://localhost:8501
```

Si el puerto 8501 esta ocupado, Streamlit elegira otro, por ejemplo `8502`. Utiliza la URL que aparezca en la terminal.

La pagina `Amortizacion Hipotecaria` aparecera automaticamente en el menu lateral porque esta dentro de la carpeta `pages`.

## Uso recomendado

1. Abre `Optimizador Hipotecario`.
2. Introduce el precio del inmueble, porcentaje financiado, impuestos, gastos, ahorros, plazo y tipo de interes.
3. Edita la tabla de productos vinculados.
4. Marca como obligatorios los productos que el banco exige contratar, aunque se puedan contratar externamente.
5. Pulsa `Calcular todos los escenarios`.
6. Revisa el escenario optimo, la tabla de contratacion y el Top 10.
7. Accede a `Amortizacion Hipotecaria` desde el menu lateral.
8. Introduce la aportacion mensual extra y el mes de inicio.
9. Revisa la comparativa mensual y simula una venta en el mes que quieras analizar.

## Regla de productos obligatorios

Cada producto tiene tres estados posibles:

| Estado | Significado | Bonificacion |
|---|---|---|
| `No` | No contratado | 0% |
| `Banco` | Contratado con el banco | Se aplica la bonificacion configurada |
| `Externo` | Contratado fuera del banco | 0% |

Cuando un producto esta marcado como obligatorio, el optimizador solo genera los estados `Banco` y `Externo`. Por tanto, no se muestran escenarios que incumplan la condicion del banco.

## Configuraciones y archivos Excel

- Las configuraciones se guardan como archivos `.json` en la carpeta del proyecto cuando se utiliza la opcion de guardar.
- Tambien se pueden cargar mediante el control de subida de archivos.
- Los resultados se exportan a archivos `.xlsx` usando `openpyxl`.
- Los archivos JSON y Excel generados pueden contener datos financieros introducidos por el usuario. Comparte estos archivos solo con personas autorizadas.

## Compartir la aplicacion

### Compartir la carpeta

Puedes comprimir la carpeta `Hipotecas` o compartirla mediante OneDrive. La otra persona necesitara:

1. Tener Python instalado.
2. Copiar o sincronizar la carpeta.
3. Instalar las dependencias con `python -m pip install -r requirements.txt`.
4. Ejecutar `streamlit run Optimizador_Hipotecario.py`.

Cada ordenador ejecutara su propia instancia de Streamlit.

### Compartir en una red local

Si ambos equipos estan en la misma red, puedes iniciar Streamlit permitiendo conexiones externas:

```powershell
streamlit run Optimizador_Hipotecario.py --server.address 0.0.0.0
```

Busca la direccion `Network URL` que muestre Streamlit y compartela con tu companero. El firewall de Windows puede pedir permiso para permitir el acceso.

Esta opcion solo funciona mientras tu ordenador y la terminal de Streamlit esten encendidos y conectados a la misma red.

### Publicar en internet

Para que pueda acceder desde cualquier lugar, necesitas desplegar el proyecto en un servicio compatible con Streamlit, por ejemplo Streamlit Community Cloud, Azure o una maquina virtual. En ese caso, no publiques datos financieros reales ni credenciales en el repositorio.

## Detener la aplicacion

En la terminal donde se esta ejecutando Streamlit, pulsa:

```text
Ctrl + C
```

## Comprobaciones rapidas

Para comprobar que los archivos Python tienen sintaxis correcta:

```powershell
python -m py_compile Optimizador_Hipotecario.py amortization.py mortgage.py optimizer.py utils.py
```

Para comprobar que las dependencias estan instaladas:

```powershell
python -m pip show streamlit pandas numpy numpy-financial plotly openpyxl
```

## Consideraciones financieras

Los calculos son simulaciones orientativas. No sustituyen una oferta vinculante del banco, asesoramiento financiero, fiscal o legal. Las condiciones reales pueden incluir comisiones, seguros, impuestos, gastos y reglas de amortizacion diferentes.
