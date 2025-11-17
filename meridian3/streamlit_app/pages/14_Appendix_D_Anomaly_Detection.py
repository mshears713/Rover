"""
Appendix D: How Anomalies are Detected

TEACHING FOCUS:
    - Threshold-based detection algorithms
    - Rate-of-change and derivative monitoring
    - Statistical anomaly scoring (z-scores)
    - Alert prioritization and classification

NARRATIVE:
    This appendix explains how the system identifies anomalous behavior
    in telemetry data. It covers multiple detection strategies, from
    simple thresholds to statistical methods, and how alerts are
    prioritized.

LEARNING OBJECTIVES:
    - Understand anomaly detection strategies
    - Learn threshold and statistical methods
    - See alert classification in practice
    - Master the anomaly detection pipeline

Documentation from Phase 4 comprehensive documentation.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Appendix D: Anomaly Detection",
    page_icon="🎯",
    layout="wide"
)

# Read and display the markdown documentation
docs_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'docs',
    'Appendix_D_Anomaly_Detection.md'
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
