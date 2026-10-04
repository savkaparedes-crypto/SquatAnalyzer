# SquatAnalyzer

Interfaz web académica para el análisis cuantitativo de una sentadilla a partir de video.

## Objetivo

Estimar el ángulo de la rodilla durante una sentadilla y visualizar su variación en el tiempo. La aplicación también estima repeticiones mediante un umbral configurable.

## Flujo

1. El usuario carga un video.
2. MediaPipe Pose detecta puntos corporales.
3. Se utilizan cadera, rodilla y tobillo derechos.
4. Se calcula el ángulo de rodilla mediante geometría vectorial.
5. La señal se interpola y suaviza.
6. Se detectan mínimos de la señal para estimar repeticiones.
7. Se muestran resultados y una gráfica interactiva.
8. Los datos pueden descargarse en CSV.

## Instalación local

Se recomienda Python 3.10 u 3.11.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

En Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Video recomendado

Para una detección más estable:
- cuerpo completo visible;
- cámara fija;
- buena iluminación;
- plano lateral o ligeramente oblicuo;
- 3 a 5 repeticiones;
- evitar que otras personas oculten el cuerpo.

## Variable analizada

**Ángulo de rodilla (grados)**, calculado con los puntos de cadera, rodilla y tobillo.

## Limitaciones

La estimación depende de la calidad del video, oclusiones, perspectiva y precisión de la estimación de pose. Los resultados son descriptivos y educativos; no constituyen diagnóstico clínico ni determinan por sí solos la corrección técnica de una sentadilla.
