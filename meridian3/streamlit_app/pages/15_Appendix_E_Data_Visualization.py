"""
Appendix E: How Data is Visualized

TEACHING FOCUS:
    - Plotting strategies for time-series telemetry
    - Interactive visualization with Plotly
    - Statistical distribution displays
    - Real-time monitoring dashboards

NARRATIVE:
    This appendix covers the visualization layer of the Meridian-3
    system. It explains how raw data becomes meaningful charts,
    graphs, and dashboards for mission monitoring.

LEARNING OBJECTIVES:
    - Understand visualization best practices
    - Learn Plotly and Matplotlib techniques
    - See real-time dashboard implementation
    - Master the data visualization pipeline

Documentation from Phase 4 comprehensive documentation.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Appendix E: Data Visualization",
    page_icon="📊",
    layout="wide"
)

# Read and display the markdown documentation
docs_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'docs',
    'Appendix_E_Data_Visualization.md'
)

try:
    with open(docs_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    st.markdown(markdown_content, unsafe_allow_html=True)

except FileNotFoundError:
    st.error(f"Documentation file not found at: {docs_path}")
    st.info("Please ensure the documentation files are in the docs/ directory.")
except Exception as e:
    st.error(f"Error loading documentation: {str(e)}")
