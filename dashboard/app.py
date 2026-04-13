import streamlit as st
import time
import httpx
import pandas as pd
import plotly.express as px

API_BASE_URL = "http://localhost:8000/api/v1"

# Page Configuration
st.set_page_config(page_title="RTUIDS Dashboard", layout="wide", page_icon="🌆")

st.title("🏙️ Real-Time Urban Intelligence System (RTUIDS)")
st.markdown("Live monitoring of massive-scale IoT sensor ingestion and machine-learning driven anomaly detection. Powered by **FastAPI**, **Redis Streams**, and **Isolation Forests**.")

# We use an empty placeholder to update the UI without reloading the entire browser tab
placeholder = st.empty()

while True:
    try:
        metrics_resp = httpx.get(f"{API_BASE_URL}/metrics", timeout=2.0)
        alerts_resp = httpx.get(f"{API_BASE_URL}/alerts", params={"limit": 500}, timeout=2.0)
        
        if metrics_resp.status_code == 200 and alerts_resp.status_code == 200:
            metrics = metrics_resp.json()
            alerts = alerts_resp.json()
            
            with placeholder.container():
                # Top KPI Row
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Total Events Processed", f"{metrics['total_events']:,}")
                
                # We color the anomaly rate delta inversely (so higher is red)
                col2.metric("Anomalies Detected", f"{metrics['total_anomalies']:,}", f"{metrics['anomaly_rate']}% Hit Rate", delta_color="inverse")
                
                col3.metric("High Severity Alerts", f"{metrics['high_severity']:,}")
                col4.metric("System Status", "🟢 Healthy", "Listening to Redis")
                
                st.divider()
                
                if alerts:
                    df = pd.DataFrame(alerts)
                    # Convert to localized readable datetime if needed
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Split into two columns for charts
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.subheader("Anomaly Classification Map")
                        fig_pie = px.pie(df, names='classification', hole=0.3)
                        fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_pie, use_container_width=True)
                        
                    with c2:
                        st.subheader("Severity Breakdown")
                        sev_counts = df['severity'].value_counts().reset_index()
                        sev_counts.columns = ['Severity', 'Count']
                        fig_bar = px.bar(
                            sev_counts, 
                            x='Severity', 
                            y='Count', 
                            color='Severity',
                            color_discrete_map={"HIGH": "#ff4b4b", "MEDIUM": "#ffa62b", "LOW": "#fcdf03"}
                        )
                        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                    st.subheader("🚨 Live Event Log (Recent Anomalies)")
                    # Reorder and filter columns for clean display
                    display_df = df[['timestamp', 'severity', 'classification', 'detected_by', 'description']]
                    st.dataframe(
                        display_df.style.applymap(
                            lambda x: "background-color: #ff4b4b" if x == "HIGH" else ("background-color: #ffa62b" if x == "MEDIUM" else ""),
                            subset=['severity']
                        ),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No anomalies detected in the stream yet! Please start the `generator.py` script.")
                    
        else:
            with placeholder.container():
                st.warning(f"Backend returned non-200 status code.")
                
    except httpx.ConnectError:
        with placeholder.container():
            st.error("Cannot connect to FastAPI Backend (`http://localhost:8000`). Please ensure the uvicorn server is running.")
    except Exception as e:
        with placeholder.container():
            st.error(f"Unexpected error: {e}")

    # Auto-refresh interval (seconds)
    time.sleep(2)
