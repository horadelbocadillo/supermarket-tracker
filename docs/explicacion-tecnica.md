# Cómo funciona el Supermarket Tracker — Guía técnica

---

## 1. Qué hace la aplicación, en términos de máquina

Cada día, a las 8:00, la aplicación se despierta automáticamente, visita las páginas web de 5 supermercados, extrae los precios de tus productos, los almacena en una base de datos local y, si detecta que algún precio está en su punto más bajo histórico, te manda un mensaje por Telegram.

Eso es todo. Simple por fuera, con varias capas por dentro.

---

## 2. Las capas del sistema

La aplicación se divide en **4 capas independientes** que se comunican entre sí:

```
┌─────────────────────────────────────────────┐
│              SCHEDULER (reloj)              │  ← despierta todo
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              SCRAPERS (ojos)                │  ← van a buscar los precios
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              SQLite (memoria)               │  ← guarda todo
└──────────┬──────────────────┬───────────────┘
           │                  │
┌──────────▼──────┐  ┌────────▼───────────────┐
│  Bot Telegram   │  │  Dashboard web         │
│  (notificador) │  │  (visualizador)        │
└─────────────────┘  └────────────────────────┘
```

---

## 3. El Scheduler — el reloj del sistema

**¿Qué es un scheduler?**
Un scheduler (del inglés *to schedule*, programar) es un componente que ejecuta tareas de forma automática en momentos concretos, sin que nadie tenga que pulsar ningún botón. Es el equivalente al temporizador de una lavadora.

**¿Por qué APScheduler?**
Hemos elegido **APScheduler** (*Advanced Python Scheduler*), una librería de Python muy consolidada. La alternativa habitual sería un **cron job** (una instrucción del sistema operativo que ejecuta scripts a horas fijas), pero tiene un problema: si la aplicación vive en la nube (Railway), no tenemos acceso al sistema operativo subyacente para configurar cron. APScheduler resuelve esto porque el reloj vive *dentro* de la propia aplicación, sin depender del sistema operativo.

**Cómo funciona:**
La aplicación arranca, APScheduler registra una tarea — "a las 08:00 UTC ejecuta la función `run_daily_scrape`" — y espera. Cuando llega la hora, lanza el proceso de scraping, y vuelve a esperar hasta el día siguiente.

---

## 4. Los Scrapers — cómo se extrae el precio de una web

**¿Qué es el scraping?**
El *web scraping* (literalmente, "rascar la web") es la técnica de leer el contenido de una página web de forma automatizada y extraer datos concretos de ella — en nuestro caso, el precio de un producto. Es lo que haría un humano que abre la web, busca el número del precio y lo apunta, pero hecho por código en milisegundos.

### El problema: no todas las webs son iguales

Las páginas web se construyen de dos formas fundamentalmente distintas:

**a) HTML estático**
El servidor envía directamente el contenido ya formado. Es como recibir una carta impresa: lees el texto tal cual llega.

**b) HTML dinámico (renderizado con JavaScript)**
El servidor envía una página casi vacía, y es el navegador del usuario el que, ejecutando código JavaScript, construye el contenido visible. Es como recibir una carta en clave que solo se descifra con un programa específico.

Esto explica por qué usamos **herramientas distintas según el supermercado**:

---

### Mercadona y Carrefour — API JSON interna

**¿Qué es una API?**
Una API (*Application Programming Interface*, interfaz de programación de aplicaciones) es un canal de comunicación entre sistemas. En la práctica: una URL a la que le haces una pregunta ("¿cuánto cuesta este producto?") y te responde con datos estructurados, no con una página web.

**¿Qué es JSON?**
JSON (*JavaScript Object Notation*) es un formato de texto para representar datos de forma ordenada. En lugar de una página web llena de imágenes y botones, recibes algo así:
```json
{ "nombre": "Leche Hacendado 1L", "precio": 0.65, "unidad": "€/L" }
```
Limpio, directo, fácil de leer para una máquina.

Mercadona y Carrefour tienen APIs internas que sus propias apps móviles usan para mostrar precios. Estas APIs no son públicas (no están documentadas oficialmente) pero son accesibles. Nuestro scraper las llama directamente, igual que haría la app del supermercado, y obtiene el precio en formato JSON. Es la técnica más fiable y rápida porque evita tener que interpretar una página web entera.

---

### Lidl y El Corte Inglés — Playwright

**¿Qué es Playwright?**
Playwright es una librería que controla un navegador web real (Chrome, en nuestro caso) desde código Python. Es un navegador sin pantalla — llamado **headless browser** (*navegador sin cabeza*, es decir, sin interfaz visual) — que carga la página, ejecuta el JavaScript, espera a que aparezca el precio y luego lo lee.

**¿Por qué es necesario?**
Lidl y El Corte Inglés construyen sus páginas con frameworks de JavaScript como React (una librería de Meta para construir interfaces web). Si intentásemos leer el HTML directamente sin ejecutar el JavaScript, veríamos la página vacía — el precio no estaría ahí todavía.

Playwright resuelve esto: carga la página exactamente como lo haría tu navegador, espera a que el precio aparezca en pantalla y lo captura.

**El coste:** es más lento (3-8 segundos por producto) y consume más memoria que leer una API directamente. Por eso solo lo usamos donde no queda más remedio.

---

### El Jamón — BeautifulSoup

**¿Qué es BeautifulSoup?**
BeautifulSoup es una librería de Python para leer y navegar por HTML. Su nombre viene de la expresión inglesa *beautiful soup* ("sopa hermosa"), que hace referencia al HTML mal formado o caótico que habitualmente se encuentra en webs reales.

**¿Cómo funciona?**
Descargamos el HTML de la página con **httpx** (una librería para hacer peticiones HTTP, el protocolo de comunicación de la web) y BeautifulSoup lo convierte en una estructura navegable. Luego le decimos: "busca el elemento con la clase CSS `price`" y nos devuelve el texto del precio.

**¿Por qué no usarlo para todos?**
Porque no funciona con páginas dinámicas (las que usan JavaScript). BeautifulSoup lee el HTML tal cual llega del servidor — si el precio lo genera JavaScript después, no lo verá.

---

### Medidas anti-bloqueo

Los supermercados detectan el tráfico automatizado y pueden bloquearlo. Para evitarlo:

- **User-Agent**: cada petición incluye una cabecera que identifica al "navegador". Usamos uno que imita a un navegador normal en lugar de identificarnos como un bot.
- **Delays aleatorios**: entre cada scraping esperamos entre 1 y 4 segundos de forma aleatoria. Un humano no visita 20 páginas en 0.001 segundos; nosotros tampoco.

---

## 5. SQLite — la memoria del sistema

**¿Qué es una base de datos?**
Una base de datos es un sistema organizado para almacenar y recuperar información de forma eficiente. Es el equivalente a una hoja de cálculo muy potente, estructurada en tablas con filas y columnas.

**¿Qué es SQL?**
SQL (*Structured Query Language*, lenguaje de consulta estructurado) es el lenguaje estándar para hablar con bases de datos. Con él puedes crear tablas, insertar datos, consultarlos y eliminarlos.

**¿Por qué SQLite y no PostgreSQL o MySQL?**
SQLite es una base de datos **embebida**: en lugar de ser un servidor independiente al que hay que conectarse, es simplemente un fichero en el disco. No necesita instalación, no consume recursos en reposo, no tiene configuración.

Para este proyecto es la elección perfecta porque:
- Solo hay un usuario (tú)
- El volumen de datos es pequeño (un precio por producto al día)
- Railway permite persistir ficheros en disco sin coste adicional

PostgreSQL o MySQL serían como contratar un almacén industrial para guardar los calcetines de casa. Excesivo.

**Nuestras tablas:**

| Tabla | Para qué sirve |
|-------|---------------|
| `products` | Lista fija de productos a vigilar |
| `price_history` | Un registro por producto por día, con el precio y la fecha |

---

## 6. La lógica de oferta — el cerebro del sistema

Guardamos un precio cada día. Con el tiempo, acumulamos suficiente historia para saber cuál es el precio "normal" de un producto.

**¿Qué es la mediana?**
La mediana es el valor central de una serie de números ordenados. Si los precios históricos de un producto fueran `[0.65, 0.70, 0.65, 0.72, 0.68]`, la mediana sería `0.68`.

Usamos la mediana en lugar de la media (el promedio) porque es más robusta ante valores extremos. Si una semana el precio se dispara a 5€ por error, la media se distorsiona; la mediana apenas se mueve.

**Criterio de oferta (los dos deben cumplirse):**

1. El precio de hoy es **menor que la mediana histórica** → está más barato de lo habitual
2. El precio de hoy es el **más bajo de los últimos 30 días** → está en su punto mínimo reciente

Solo cuando ambas condiciones son verdaderas consideramos que hay oferta. Esto evita falsos positivos: un precio puede estar ligeramente por debajo de la mediana sin ser realmente una oportunidad de compra.

**Periodo de arranque:**
Los primeros 7 días no hay suficiente historia para calcular nada fiable. Durante ese periodo el sistema simplemente muestra el precio sin indicador de oferta.

---

## 7. FastAPI — el servidor web del dashboard

**¿Qué es un servidor web?**
Un servidor web es un programa que escucha peticiones de navegadores y les responde con páginas HTML, datos, imágenes, etc. Cuando escribes una URL en tu navegador, tu ordenador hace una petición a un servidor web; el servidor responde con el contenido que ves.

**¿Qué es FastAPI?**
FastAPI es un framework (*marco de trabajo*: una estructura de código que resuelve problemas comunes para que tú no tengas que reinventarlos) para construir servidores web en Python. Es moderno, rápido y con muy poco código consigues mucho.

**¿Qué es Jinja2?**
Jinja2 es un motor de plantillas (*template engine*): permite escribir HTML con "huecos" que el servidor rellena con datos reales antes de enviarlo al navegador. Por ejemplo:

```html
<span>{{ producto.nombre }}</span> → <span>Leche Hacendado 1L</span>
```

**Chart.js y Tailwind CSS vía CDN:**
- **Chart.js**: librería JavaScript para dibujar gráficas en el navegador. La cargamos desde un CDN (*Content Delivery Network*, red de distribución de contenidos: servidores repartidos por el mundo que sirven ficheros estáticos muy rápido) sin necesidad de instalar nada.
- **Tailwind CSS**: framework de estilos visuales que aplica diseño mediante clases CSS predefinidas. En lugar de escribir `color: green; font-weight: bold;`, escribes `text-green-700 font-semibold`. También vía CDN.

---

## 8. El Bot de Telegram

**¿Qué es un bot de Telegram?**
Un bot es una cuenta de Telegram controlada por un programa en lugar de por un humano. Telegram ofrece una API oficial y gratuita para crear bots. El proceso es:

1. Hablas con **@BotFather** (el bot oficial de Telegram para crear bots) y obtienes un **token** — una cadena de texto larga y única que identifica tu bot, como una contraseña.
2. Obtienes tu **chat_id** — el identificador numérico de tu conversación con el bot.
3. Tu aplicación usa la librería **python-telegram-bot** para enviar mensajes a ese chat_id usando ese token.

Esto es completamente gratuito, sin límites para uso personal, y no requiere ningún número de teléfono adicional ni cuenta de empresa.

---

## 9. Railway — dónde vive la aplicación

**¿Qué es un servidor en la nube?**
En lugar de que la aplicación corra en tu ordenador (que se apaga, se queda sin batería, se desconecta de internet), la ejecutamos en un ordenador de otra empresa que está siempre encendido y conectado.

**¿Por qué Railway?**
Railway es una plataforma de **PaaS** (*Platform as a Service*, plataforma como servicio): le das tu código, y ellos se encargan de todo lo demás — instalar dependencias, arrancar el servidor, mantenerlo encendido. No necesitas saber de infraestructura.

En su plan gratuito ofrece **750 horas de cómputo al mes** — suficiente para mantener una aplicación encendida las 24 horas los 31 días del mes (744 horas). Coste: cero euros.

**Variables de entorno:**
El token de Telegram y tu chat_id son datos sensibles que **no deben** guardarse en el código (si alguien accede al repositorio, tendría acceso a tu bot). Se almacenan como **variables de entorno** — configuración externa que la aplicación lee al arrancar, sin que esté escrita en ningún fichero.

---

## 10. El flujo completo, de principio a fin

```
08:00 UTC
   │
   ├── APScheduler dispara run_daily_scrape()
   │
   ├── Para cada producto en products.json:
   │    ├── Llama al scraper correspondiente
   │    ├── El scraper devuelve { price: 0.65, available: true }
   │    ├── Se guarda el precio en price_history (SQLite)
   │    └── Se evalúa si es oferta (mediana + mínimo 30d)
   │
   ├── Si hay ofertas:
   │    └── Bot de Telegram envía mensaje con la lista
   │
   └── Fin. El scheduler vuelve a dormirse hasta mañana.

En cualquier momento:
   └── Abres el dashboard en el navegador
        ├── FastAPI consulta SQLite
        ├── Jinja2 construye el HTML con los datos
        └── Ves precio actual + indicador de oferta
```

---

Este es el sistema completo. Cada pieza tiene una responsabilidad única y están desacopladas — si el bot de Telegram falla, el scraping sigue funcionando; si el dashboard está caído, las alertas siguen llegando. Eso es lo que en ingeniería de software llamamos **separación de responsabilidades**, uno de los principios más importantes en el diseño de sistemas robustos.
