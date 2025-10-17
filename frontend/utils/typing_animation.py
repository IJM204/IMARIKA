import streamlit as st
import time

def show_typing_animation(message="Imarika is thinking..."):
    """Show typing animation while processing"""
    
    placeholder = st.empty()
    
    dots = ""
    for i in range(3):
        dots += "."
        placeholder.markdown(f"""
        <div style="display: flex; align-items: center; padding: 1rem; background: #F0F8F0; border-radius: 10px; margin: 1rem 0;">
            <div style="font-size: 1.2rem; margin-right: 0.5rem;">🌾</div>
            <div style="color: #2E8B57;">{message}{dots}</div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.5)
    
    placeholder.empty()

def show_processing_status(status="Processing your query..."):
    """Show processing status with spinner"""
    
    return st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 2rem; background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%); border-radius: 15px; margin: 1rem 0;">
        <div style="margin-right: 1rem;">
            <div style="width: 20px; height: 20px; border: 2px solid #2E8B57; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        </div>
        <div style="color: #2E8B57; font-weight: 600;">{status}</div>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)