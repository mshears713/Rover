"""
Appendix C: How Data Gets Cleaned

TEACHING FOCUS:
    - Data validation and range checking
    - Interpolation strategies for missing data
    - Reconstruction techniques for corrupted values
    - Quality metrics and reporting

NARRATIVE:
    This appendix details how corrupted and incomplete telemetry is
    cleaned and validated. It covers range checking, interpolation,
    reconstruction algorithms, and quality assessment.

LEARNING OBJECTIVES:
    - Understand data cleaning strategies
    - Learn interpolation and reconstruction methods
    - See validation and quality metrics in action
    - Master the data cleaning pipeline

Documentation from Phase 4 comprehensive documentation.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Appendix C: Data Cleaning",
    page_icon="🔧",
    layout="wide"
)

# Read and display the markdown documentation
docs_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'docs',
    'Appendix_C_Data_Cleaning.md'
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
