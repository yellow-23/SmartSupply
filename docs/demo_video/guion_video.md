# Guion video - SmartSupply (version simple)

Duracion: unos 15 minutos. Lo que va entre comillas es lo que dices. Lo demas es lo que haces en pantalla.

Links:
- App: https://smartsupply-frontend.pages.dev
- Backend (Render): https://smartsupply-e6g8.onrender.com/docs
- Base de datos: Supabase, proyecto `xqiehkshtedrodhtdkzv`

---

## Antes de grabar

- Ten una cuenta de prueba nueva, sin datos, ya confirmada por correo.
- Ten los archivos de prueba en el escritorio (carpeta `docs/demo_video/datos/`).
- Abre estas pestanas: VS Code, la app, Supabase, Render, Cloudflare, GitHub, Resend, tu correo.
- Sube todos los archivos primero. Despues corre las predicciones (si cambias datos, hay que repetirlas).
- Al final, revisa que no se vea ninguna clave ni contrasena.

---

## 1. Inicio (1 min)

Pantalla: login de la app.

"Hola, soy Cristobal Flores. Les muestro SmartSupply, mi proyecto de titulo de Ingenieria Civil en Informatica de la UNAB."

"Las distribuidoras chilenas guardan sus ventas en cuadernos, fotos y Excel desordenados. Por eso compran a ojo, y a veces se quedan sin producto o les sobra mucho."

"SmartSupply recibe esos datos como esten, predice cuanto se va a vender de cada producto y dice cuanto hay que pedir."

"La idea de la tesis es simple: elegir el mejor modelo de prediccion para cada producto da mejores resultados que usar el mismo modelo para todos."

---

## 2. El codigo (4 min)

Pantalla: VS Code.

**Carpetas principales** (muestra la raiz del proyecto)

"El proyecto tiene varias carpetas:"
- `backend`: "la API, que es el cerebro. Esta hecha con FastAPI (Python)."
- `frontend`: "lo que ve el usuario. Esta hecho con React."
- `forecasting`: "los modelos que predicen las ventas."
- `inventory`: "los calculos de cuanto y cuando pedir."
- `etl`: "los scripts para cargar el dataset de prueba."
- `docs`: "la tesis y los diagramas."

**Backend** (abre `backend/app`)

"En `api` hay un archivo por tema: login, ventas, predicciones, inventario, ordenes, productos y el asistente Stocky."
"En `services` esta la logica: leer archivos con IA, revisar la calidad de los datos, predecir y calcular inventario."
"En `models` estan las tablas de la base de datos."
Abre `api/auth.py`: "Aqui se revisa quien es el usuario, y que solo vea los datos de su negocio."

**Predicciones** (abre `forecasting/src`)

"Aqui estan cuatro modelos: ARIMA, Prophet, XGBoost y LSTM. El selector automatico, que llamamos AMS, prueba varios con cada producto y se queda con el que se equivoca menos."

**Inventario** (abre `inventory/src`)

"Aqui se calcula la cantidad ideal de pedido, y el nivel minimo de stock para pedir de nuevo."

**Frontend** (abre `frontend/src/features`)

"Una carpeta por pantalla: dashboard, predicciones, inventario, ordenes, productos, ingesta y datos."

**Pruebas** (en la terminal)
```bash
cd backend && PYTHONPATH=. ../venv/bin/python3.11 -m pytest tests/ -q
```
"Tambien hay pruebas automaticas que revisan que todo siga funcionando."

---

## 3. Donde vive el sistema (3 min)

**Supabase (base de datos)**

Pantalla: Supabase, Table Editor.
"Aqui estan los datos. Por ejemplo `sales_history` guarda las ventas, `products` los productos, `stock_levels` el stock y `purchase_orders` las ordenes de compra."
"Cada archivo que se sube queda registrado en `ingest_log`. Asi se puede deshacer una carga."
Muestra Authentication > Users: "Aqui estan los usuarios y el login con Google."
No muestres la pestana de claves (API keys).

**Render (backend)**

Pantalla: Render.
"El backend esta en Render. Cada vez que subo cambios a GitHub, se actualiza solo."
Muestra Logs y Events. Abre `/docs`: "Esta es la lista de todas las funciones de la API."

**Cloudflare (frontend)**

Pantalla: Cloudflare Pages.
"La pagina web esta en Cloudflare. Tambien se actualiza sola con cada cambio en GitHub."

**Resend (correos)**

Pantalla: Resend.
"Para los correos usamos Resend, con nuestro propio dominio. El sistema manda dos correos: uno cada dia si algun producto tiene poco stock, y un resumen cada lunes."
Muestra GitHub > Actions: "Esto lo programa GitHub: cada dia llama al backend y el backend manda los correos."

---

## 4. La app funcionando (7 min)

Pantalla: la app, con la cuenta de prueba.

**a) Entrar (30 s)**
Inicia sesion. Si pide el nombre del negocio, escribe "Distribuidora Demo".
"El login funciona con correo o con Google. Al entrar por primera vez se crea el negocio solo."

**b) Subir ventas (1 min)**
Ingesta > sube `ventas_demo_limpio.csv`.
"Subo un archivo de ventas. El sistema lo lee y me muestra lo que entendio antes de guardar. Si algo esta mal, no se guarda nada."
Elige negocio y ubicacion, marca "Unidades" y confirma.

**c) Un archivo desordenado (1 min)**
Sube `ventas_distribuidora_desordenado.xlsx`. No confirmes.
"Este Excel es desordenado, con titulos y nombres raros. La IA igual lo entiende. Tambien lee fotos y PDF."

**d) Archivo con errores (1 min)**
Sube `ventas_con_problemas.csv`.
"Aqui el sistema avisa de dos problemas: hay fechas futuras, y hay datos mensuales mezclados con diarios. Este ultimo error bloquea la carga, para no dañar las predicciones."

**e) Productos y stock (1 min)**
Sube `catalogo_demo.csv` y confirma. Luego `stock_demo.csv` y confirma. Abre Productos.
"El mismo lugar sirve para subir el catalogo con costos y el stock actual. El sistema distingue solo de que es cada archivo."

**f) Datos (45 s)**
Abre Datos.
"Aqui veo cada archivo subido. Puedo editar una fila, borrarla, o deshacer toda la carga."

**g) Predicciones (2 min)**
Forecasting > BEBIDAS > 14 dias > Generar. Espera.
"El sistema prueba varios modelos con este producto y elige el mejor. Aqui se ve el modelo ganador y su error."
Repite con PANADERIA o LIMPIEZA: "Cada producto puede tener un modelo ganador distinto."
Exporta el PDF. Muestra "Dataset de referencia": "Tambien probamos con un dataset publico de Corporacion Favorita para validar la idea."

**h) Dashboard (30 s)**
Abre Dashboard.
"Aqui veo lo importante de un vistazo: productos en alerta, ordenes pendientes y las ventas de las ultimas semanas, con la prediccion."

**i) Inventario y ordenes (1 min 30 s)**
Inventario: "Cada producto aparece como critico o normal segun su stock." Haz clic en BEBIDAS para ver cuanto y cuando pedir.
Boton "Generar ordenes". Abre Ordenes: cambia una a "Confirmada".
"Con un clic se crean las ordenes de compra de lo que falta."

**j) Stocky (1 min)**
Boton naranja abajo a la derecha. Escribe:
1. "Que productos estan en riesgo?"
2. "Tengo 500 unidades de BEBIDAS en bodega"
"Stocky es un asistente. Le pregunto en lenguaje normal y consulta o cambia los datos."

**k) Correos (45 s)**
Muestra tu correo con el aviso de stock bajo y el resumen semanal. Muestra tambien Resend con los envios.
Para enviarlos justo antes de grabar (cambia `<ID>` por el id de tu negocio demo):
```bash
gh workflow run stocky-notify.yml -R yellow-23/SmartSupply -f job=low-stock -f business_id=<ID>
gh workflow run stocky-notify.yml -R yellow-23/SmartSupply -f job=weekly-digest -f business_id=<ID>
```
"El sistema avisa solo. El dueño no tiene que entrar a revisar."

---

## 5. Cierre (30 s)

Pantalla: Dashboard.

"En resumen: el usuario sube sus datos como los tenga, el sistema predice las ventas de cada producto, calcula cuanto pedir y genera las ordenes. Todo funciona en internet: Render, Cloudflare y Supabase. Gracias."

---

## Archivos de prueba

Estan en `docs/demo_video/datos/`:

| Archivo | Para que sirve |
|---------|----------------|
| `ventas_demo_limpio.csv` | Ventas de 6 meses de 6 productos |
| `catalogo_demo.csv` | Costos y plazos de cada producto |
| `stock_demo.csv` | Stock actual de cada producto |
| `ventas_con_problemas.csv` | Para mostrar los avisos de calidad |

Ya existentes en `datasets/test_ingest/`: `ventas_distribuidora_desordenado.xlsx` (Excel desordenado), `reporte_ambiguo.csv`, `reporte_semanal.pdf`.

Productos: BEBIDAS, LACTEOS, ABARROTES, PANADERIA, LIMPIEZA, CONGELADOS.

---

## Si algo falla

- La prediccion tarda mucho: es normal (hasta 1 o 2 minutos). Corta esa parte al editar.
- La IA da error al leer un archivo: reintenta en un minuto, o usa el CSV limpio, que no necesita IA.
- Todo sale "critico": sube `stock_demo.csv` antes.
- No llegan los correos: revisa que el negocio demo tenga como dueño tu correo, y que haya productos criticos.
- Si te pasas de tiempo, salta: archivo desordenado (c), Dashboard (h) y la parte de Cloudflare.
