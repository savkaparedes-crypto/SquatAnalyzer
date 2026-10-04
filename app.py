import os
import tempfile

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.pose_analysis import analyze_video
from src.biomechanics import calculate_summary, detect_squat_repetitions

st.set_page_config(
    page_title="SquatAnalyzer",
    page_icon="🏋️",
    layout="wide",
)

st.markdown("""
<style>
.main-title {font-size: 42px; font-weight: 700; margin-bottom: 0;}
.subtitle {font-size: 18px; color: #6b7280; margin-bottom: 25px;}
.small-note {font-size: 13px; color: #6b7280;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏋️ SquatAnalyzer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Evaluación cuantitativa de la sentadilla mediante análisis de video</div>',
    unsafe_allow_html=True,
)

with st.expander("📌 ¿Qué mide esta aplicación?"):
    st.write(
        """
        La aplicación utiliza un video como fuente de datos. Detecta cadera, rodilla y
        tobillo mediante estimación de pose y calcula el ángulo de la rodilla cuadro a
        cuadro. La señal temporal permite visualizar la variación del ángulo y estimar
        repeticiones según los parámetros seleccionados.
        """
    )
    st.caption(
        "Uso académico/educativo. El resultado no constituye un diagnóstico clínico "
        "ni determina por sí solo si una sentadilla es correcta o incorrecta."
    )

with st.sidebar:
    st.header("⚙️ Parámetros")
    threshold = st.slider(
        "Ángulo máximo para considerar una repetición (°)",
        min_value=90, max_value=140, value=120, step=5
    )
    min_distance = st.slider(
        "Tiempo mínimo entre repeticiones (s)",
        min_value=0.5, max_value=2.0, value=0.8, step=0.1
    )
    st.divider()
    st.caption("Variable principal: ángulo de rodilla (°).")

st.header("1. Cargar video")
uploaded = st.file_uploader(
    "Seleccione un video de una sentadilla",
    type=["mp4", "mov", "avi", "m4v"],
)

if uploaded is None:
    st.info("Carga un video para comenzar el análisis.")
    st.stop()

st.success(f"Archivo seleccionado: {uploaded.name}")
st.video(uploaded)

st.header("2. Ejecutar análisis")

if st.button("🔍 Analizar movimiento", type="primary", use_container_width=True):
    temp = None
    try:
        with st.spinner("Detectando pose y calculando ángulos..."):
            suffix = os.path.splitext(uploaded.name)[1].lower() or ".mp4"
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp.write(uploaded.getvalue())
            temp.close()

            times, angles, visibility, frames, fps = analyze_video(temp.name)
            reps = detect_squat_repetitions(
                angles, times, threshold, min_distance
            )
            summary = calculate_summary(angles, times, reps)

        if summary is None:
            st.error(
                "No fue posible detectar suficientemente la pierna. "
                "Prueba con un video de cuerpo completo, cámara estable y buena iluminación."
            )
            st.stop()

        st.success("✅ Análisis completado")

        st.header("3. Resultados principales")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Repeticiones", summary["repetitions"])
        c2.metric("Mayor flexión", f'{summary["minimum_angle"]:.1f}°')
        c3.metric("Ángulo máximo", f'{summary["maximum_angle"]:.1f}°')
        c4.metric("Duración", f'{summary["duration"]:.2f} s')

        st.header("4. Ángulo de rodilla durante el movimiento")
        df = pd.DataFrame({
            "Tiempo (s)": times,
            "Ángulo de rodilla (°)": angles,
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=angles,
            mode="lines",
            name="Ángulo de rodilla",
        ))
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            annotation_text=f"Umbral {threshold}°",
        )

        if reps:
            fig.add_trace(go.Scatter(
                x=[r["time"] for r in reps],
                y=[r["minimum_angle"] for r in reps],
                mode="markers",
                name="Máxima flexión",
                marker=dict(size=10),
            ))

        fig.update_layout(
            xaxis_title="Tiempo (s)",
            yaxis_title="Ángulo de rodilla (°)",
            template="plotly_white",
            hovermode="x unified",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.header("5. Repeticiones detectadas")
        if reps:
            rep_df = pd.DataFrame([
                {
                    "Repetición": i + 1,
                    "Tiempo máxima flexión (s)": round(r["time"], 2),
                    "Ángulo mínimo (°)": round(r["minimum_angle"], 1),
                }
                for i, r in enumerate(reps)
            ])
            st.dataframe(rep_df, use_container_width=True, hide_index=True)
        else:
            st.warning(
                "No se detectaron repeticiones con el criterio seleccionado. "
                "Prueba aumentando el umbral de flexión."
            )

        st.header("6. Calidad de detección")
        quality = float((visibility > 0.5).mean() * 100)
        st.progress(min(100, int(quality)))
        st.write(
            f"Detección adecuada en aproximadamente **{quality:.1f}%** de los cuadros."
        )

        st.header("7. Descargar resultados")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar datos en CSV",
            csv,
            "squat_analysis.csv",
            "text/csv",
            use_container_width=True,
        )

        st.header("8. Interpretación")
        if reps:
            st.info(
                f'Se detectaron **{len(reps)}** repetición(es) que alcanzaron el '
                f'criterio de flexión seleccionado. El menor ángulo registrado fue '
                f'**{summary["minimum_angle"]:.1f}°**.'
            )
        else:
            st.info(
                f'No se identificaron repeticiones que alcanzaran el umbral de '
                f'**{threshold}°**.'
            )

        st.caption(
            "Interpretación descriptiva basada en video. No corresponde a una "
            "evaluación clínica."
        )

    except Exception as e:
        st.error(f"Ocurrió un error durante el análisis: {e}")

    finally:
        if temp is not None and os.path.exists(temp.name):
            os.remove(temp.name)

st.markdown("---")
st.caption("Proyecto de Análisis Bioinstrumental del Movimiento Humano")
