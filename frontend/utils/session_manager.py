import streamlit as st

def initialize_session():
    """Initialize session state variables"""
    
    # User preferences
    if 'user_location' not in st.session_state:
        st.session_state.user_location = 'Nairobi'
    
    if 'language' not in st.session_state:
        st.session_state.language = 'English'
    
    # Chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # System state
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = True
    
    # Performance tracking
    if 'query_count' not in st.session_state:
        st.session_state.query_count = 0
    
    if 'session_start_time' not in st.session_state:
        import time
        st.session_state.session_start_time = time.time()

def get_session_stats():
    """Get session statistics"""
    import time
    
    current_time = time.time()
    session_duration = current_time - st.session_state.get('session_start_time', current_time)
    
    return {
        'query_count': st.session_state.get('query_count', 0),
        'session_duration': session_duration,
        'messages_count': len(st.session_state.get('messages', [])),
        'user_location': st.session_state.get('user_location', 'Unknown'),
        'language': st.session_state.get('language', 'English')
    }