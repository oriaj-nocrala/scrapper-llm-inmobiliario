---

# Guía Completa de Web Scraping para Assetplan (Corregida)

Este documento consolida el análisis de las diferentes secciones del sitio web `assetplan.cl`, proporcionando una guía paso a paso para construir un scraper.

**Nota Importante:** El sitio utiliza **Alpine.js** y **Livewire** para la interactividad. Esto significa que el contenido se carga y modifica dinámicamente. Para un scraping efectivo, es **esencial utilizar una herramienta que ejecute JavaScript**, como **Selenium** o **Playwright**.

---

## **Parte 1: Página Principal de Búsqueda (`/arriendo/departamento`)**

Esta es la página de inicio donde el usuario puede buscar, filtrar y ver una lista de edificios con departamentos en arriendo.

### **1.1. Cabecera y Navegación**

La cabecera contiene la barra de búsqueda principal y menús de navegación.

| Elemento | Selector Clave | Notas |
| :--- | :--- | :--- |
| **Input de Búsqueda** | `input[id="header_search_bar"]` | Para buscar por comuna o ciudad. Los resultados de autocompletado se generan dinámicamente. |
| **Menú "Propietarios"**| `button` con texto `Propietarios` | Despliega un submenú con enlaces a "Publica tu propiedad" y "Invierte con nosotros". |
| **Enlace "Ayuda"** | `a[href*="ayuda.assetplan.cl"]` | Abre la sección de ayuda en una nueva pestaña. |
| **Menú Móvil** | `nav-mobile` | Contiene versiones adaptadas de los menús de escritorio, además de "Pagar arriendo" e "Iniciar sesión". |

### **1.2. Aplicación de Filtros (Barra Lateral)**

La barra lateral permite refinar la búsqueda. Para aplicar un filtro, se debe localizar el `input` (checkbox o radio) y simular un clic.

| Filtro | Selector de Ejemplo | Tipo |
| :--- | :--- | :--- |
| **Rango de Precio** | `input[name="min-price"]`, `input[name="max-price"]` | `text` |
| **Ordenar por** | `input[type="radio"][value="ASC"]` | `radio` |
| **Dormitorios** | `input[id="tipology-1"]` (para 1 dormitorio) | `checkbox` |
| **Baños** | `input[id="tipologyBath-1"]` (para 1 baño) | `checkbox` |
| **Características** | `input[id="hasParking"]` (para estacionamiento) | `checkbox` |
| **Beneficios** | `input[id="doesntRequireAval"]` (sin aval) | `checkbox` |
| **Descuentos** | `input[id="onOffer"]` (descuento en arriendo) | `checkbox` |
| **Ubicación** | `input[id="closeTotheMetro"]` (cercano a metro) | `checkbox` |

### **1.3. Extracción de la Lista de Edificios**

El contenido principal de la página es una lista de "tarjetas", cada una representando un edificio.

1.  **Iterar sobre cada tarjeta de edificio:**
    * **Selector CSS:** `div.building-card[data-building]`

2.  **Dentro de cada tarjeta, extraer la siguiente información:**

| Dato | Selector CSS | Atributo / Texto |
| :--- | :--- | :--- |
| **ID del Edificio** | `div.building-card` | `data-building` |
| **Nombre del Edificio**| `a.text-neutral-800.lg\:text-base` | `.text` |
| **URL del Edificio** | `a.text-neutral-800.lg\:text-base` | `href` |
| **Dirección** | `span.text-neutral-500` | `.text` |
| **Precio "Desde"** | `p.text-lg.font-bold` | `.text` |
| **URL de Imagen** | `li.splide__slide.is-visible img` | `src` |
| **Promociones** | `div.badge_promos span` | `.text` (iterar) |
| **Tipos de Depto.** | `div.space-y-1\.5 > a` | N/A |

3.  **Verificar disponibilidad por tipo de departamento:**
    * Dentro de cada tarjeta, itera sobre los enlaces de tipologías (`div.space-y-1.5 > a`).
    * Si el enlace `<a>` **NO tiene** la clase `grayscale`, la tipología está **disponible**.
    * Si el enlace `<a>` **SÍ tiene** la clase `grayscale`, la tipología **no está disponible**.

---

## **Parte 2: Página de Detalle del Edificio (`.../edificio/{id}`)**

Al hacer clic en una tarjeta de edificio, se navega a su página de detalle.

### **2.1. Información General y Comodidades**

| Dato | Selector CSS | Atributo / Texto |
| :--- | :--- | :--- |
| **Nombre del Edificio** | `h1.name-building` | `.text` |
| **Dirección** | `h2.address-building` | `.text` |
| **URLs de Galería** | `section.galery-desktop img` | `src` (iterar) |
| **Comodidades** | `div.flex.flex-row.items-center p.text-sm` | `.text` (iterar) |

### **2.2. Lista de Tipologías de Departamentos**

Esta sección muestra las diferentes configuraciones de departamentos disponibles en el edificio.

1.  **Iterar sobre cada tarjeta de tipología:**
    * **Selector CSS:** `div.grid.grid-cols-1.gap-6 > div`

2.  **Dentro de cada tarjeta, extraer:**

| Dato | Selector CSS | Atributo / Texto |
| :--- | :--- | :--- |
| **URL de Imagen** | `img.object-cover` | `src` |
| **Dormitorios y Baños**| `div.flex.gap-x-2\.5` | `.text` |
| **Superficie (m²)** | `div.flex.flex-col.space-y-1` | `.text` |
| **Valor de Arriendo** | `p.text-lg.font-semibold` | `.text` |
| **Promociones** | `div.badge_promos span` | `.text` (iterar) |
| **URL para Ver Unidades**| `a[href*="/arriendo/departamento/"]`| `href` |
| **Cantidad de Unidades**| `a[href*="/arriendo/departamento/"]`| `.text` |

---

## **Parte 3: Navegación hacia el Detalle del Departamento**

Desde la página del edificio, el camino para ver un departamento específico depende de la cantidad de unidades disponibles para una tipología.

### **Caso A: Sólo 1 unidad disponible (Navegación Directa)**

Si el botón para una tipología dice **"Ver 1 disponible"**, al hacer clic, se navega **directamente** a la página de detalle de ese único departamento. No hay un paso intermedio con un modal.

* **Acción:** Hacer clic en el enlace `a[href*="/arriendo/departamento/"]` cuyo texto sea "Ver 1 disponible".

### **Caso B: Múltiples unidades disponibles (Navegación por Modal)**

Si el botón dice **"Ver X disponibles"** (donde X es mayor que 1), al hacer clic se abre un **modal** para seleccionar la unidad.

1.  **Abrir el Modal:** Haz clic en el enlace `a.bg-blue-600` (el botón "Ver X disponibles").
2.  **Iterar sobre cada unidad en el modal:**
    * **Selector CSS:** `ul.divide-y > li`
3.  **Dentro de cada `li`, extraer los datos de la unidad:**

| Dato | Selector CSS | Atributo / Texto |
| :--- | :--- | :--- |
| **ID Interno de Unidad** | `input[type="radio"]` | `value` |
| **Número del Depto.** | `p.text-lg.font-bold` | `.text` |
| **Precio Mensual** | `span.text-base.font-bold` | `.text` |
| **Disponibilidad** | `div.chip-available` | `.text` |

4.  **Seleccionar una Unidad:** Haz clic directamente en el elemento `<li>` que representa al departamento deseado. Al hacerlo, el modal se cerrará y serás redirigido a la página de detalle de esa unidad.

---

## **Parte 4: Página de Detalle del Departamento**

Al seleccionar una unidad, se llega a la página final con todos sus detalles.

### **4.1. Resumen Principal del Departamento**

| Dato | Selector | Atributo / Texto |
| :--- | :--- | :--- |
| **Nombre de Comunidad**| `h1.title-breadcrumbs` | `.text` |
| **Número del Depto.** | `#info > div:nth-child(3) > span.text-xl` | `.text` |
| **Dirección** | `#info > div:nth-child(3) > span.text-xs` | `.text` |
| **Valor Arriendo Orig.** | `span.line-through` | `.text` |
| **Valor Arriendo Desc.** | `//p[contains(text(), 'OFF')]/following-sibling::span` (XPath) | `.text` |
| **Gasto Común** | `//span[contains(text(), 'Gasto común')]/following-sibling::span` (XPath) | `.text` |
| **Garantía** | `//span[text()='Garantía']/following-sibling::span` (XPath) | `.text` |
| **Promociones** | `div.badge_promos span.inline-flex` | `.text` (iterar) |
| **URLs de Imágenes** | `ul.splide__list img` | `src` (iterar y filtrar duplicados) |

### **4.2. Pestañas de Información Detallada**

Para acceder a esta información, primero se debe **hacer clic en la pestaña correspondiente** (`Detalle`, `Características`, etc.) usando el menú `nav#sticky-menu`.

#### **Sección "Detalle" (`id="detail"`)**

| Dato | Selector CSS | Atributo / Texto |
| :--- | :--- | :--- |
| **Código del Depto.** | `div.cod-dpt span` | `.text` |
| **Disponibilidad** | `div.chip-available` | `.text` |
| **Características** | `div.item-feature` | Iterar para obtener nombre (del tooltip) y valor. |

#### **Sección "Características" (`id="features"`)**

**Acción previa:** Haz clic en el botón **"Mostrar más"** (`//a[contains(text(), 'Mostrar más')]`) si existe, para desplegar toda la información.

| Dato | Selector XPath | Atributo / Texto |
| :--- | :--- | :--- |
| **Terminaciones** | `//h2[text()='Terminaciones']/following-sibling::ul/li` | `.text` (iterar) |
| **Equipamiento** | `//h2[text()='Equipamiento']/following-sibling::ul/li` | `.text` (iterar) |
| **Comodidades Edificio**| `//h3[contains(text(), 'Comodidades del edificio')]//div[@class='grid']/div` | `.text` (iterar) |
