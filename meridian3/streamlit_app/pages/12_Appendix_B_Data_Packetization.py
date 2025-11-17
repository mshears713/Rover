"""
Appendix B: How Data Gets Packetized

TEACHING FOCUS:
    - Frame-to-packet encoding process
    - Metadata and timestamp management
    - Packet structure and organization
    - Detailed code walkthrough with examples

NARRATIVE:
    This appendix explores how raw sensor frames are encoded into
    packets for transmission. It covers the packetization process,
    metadata handling, and the structure of transmitted data.

LEARNING OBJECTIVES:
    - Understand the packetization pipeline
    - Learn packet structure and metadata
    - See how timestamps are managed
    - Master the frame encoding architecture

Documentation from Phase 4 comprehensive documentation.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Appendix B: Data Packetization",
    page_icon="📦",
    layout="wide"
)

# Read and display the markdown documentation
docs_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'docs',
    'Appendix_B_Data_Packetization.md'
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
