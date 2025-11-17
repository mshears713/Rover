"""
Appendix A: How Sensor Data is Generated

TEACHING FOCUS:
    - Understanding the rover state representation
    - How sensors add realistic noise to measurements
    - The simulation pipeline from state to sensor readings
    - Detailed code walkthrough with examples

NARRATIVE:
    This appendix provides a deep dive into how the Meridian-3 rover
    creates sensor data from scratch. It covers the RoverState class,
    sensor noise models, and the complete data generation pipeline.

LEARNING OBJECTIVES:
    - Understand the "source of truth" rover state
    - Learn how realistic sensor noise is modeled
    - See the relationship between true state and measurements
    - Master the sensor data generation architecture

Documentation from Phase 4 comprehensive documentation.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Appendix A: Sensor Data Generation",
    page_icon="📡",
    layout="wide"
)

# Read and display the markdown documentation
docs_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'docs',
    'Appendix_A_Sensor_Data_Generation.md'
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
