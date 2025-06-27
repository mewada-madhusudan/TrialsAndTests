import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="My Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom navigation bar */
    .nav-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .nav-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    
    .nav-left, .nav-right {
        font-size: 1.5rem;
    }
    
    .nav-center {
        display: flex;
        gap: 2rem;
    }
    
    .nav-item {
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        transition: background-color 0.3s;
        font-weight: 500;
    }
    
    .nav-item:hover {
        background-color: rgba(255, 255, 255, 0.2);
        text-decoration: none;
        color: white;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        color: #2c3e50;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Notes section styling */
    .notes-container {
        background-color: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .notes-title {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Content container */
    .content-container {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Navigation bar
st.markdown("""
<div class="nav-container">
    <div class="nav-content">
        <div class="nav-left">🏠</div>
        <div class="nav-center">
            <a href="#" class="nav-item">Home</a>
            <a href="#" class="nav-item">About</a>
            <a href="#" class="nav-item">Contact</a>
        </div>
        <div class="nav-right">⚙️</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">My Dashboard</h1>', unsafe_allow_html=True)

# Create sample dataframes
@st.cache_data
def create_sample_data():
    # Table 1: Sales Data
    table1 = pd.DataFrame({
        'Product': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
        'Sales': [1200, 1500, 800, 2000, 1100],
        'Profit': [240, 300, 160, 400, 220],
        'Region': ['North', 'South', 'East', 'West', 'Central']
    })
    
    # Table 2: Employee Data
    table2 = pd.DataFrame({
        'Employee': ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson', 'Tom Brown'],
        'Department': ['IT', 'Marketing', 'Sales', 'HR', 'Finance'],
        'Salary': [75000, 65000, 70000, 60000, 68000],
        'Experience': [5, 3, 7, 4, 6]
    })
    
    # Table 3: Monthly Metrics
    table3 = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Revenue': [50000, 55000, 48000, 62000, 58000, 65000],
        'Expenses': [35000, 38000, 32000, 42000, 39000, 43000],
        'Growth': ['5%', '10%', '-4%', '12%', '8%', '15%']
    })
    
    return table1, table2, table3

# Initialize session state
if 'show_tables' not in st.session_state:
    st.session_state.show_tables = False

# Main content area
col1, col2 = st.columns([1, 3])

with col1:
    # Notes section
    st.markdown("""
    <div class="notes-container">
        <div class="notes-title">📝 Notes:</div>
        <div>
            • Click the button to load data tables<br>
            • Tables show different business metrics<br>
            • Data is automatically cached for performance<br>
            • Use the navigation bar to access different sections<br>
            • All data is sample data for demonstration
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Button to populate tables
    if st.button("📊 Download & Populate Tables", key="download_btn"):
        st.session_state.show_tables = True
        st.success("✅ Tables loaded successfully!")
    
    # Show tables if button was clicked
    if st.session_state.show_tables:
        st.markdown("---")
        
        # Get the data
        table1, table2, table3 = create_sample_data()
        
        # Display tables in columns
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.subheader("📈 Table 1: Sales Data")
            st.dataframe(table1, use_container_width=True)
            
            st.subheader("👥 Table 2: Employee Data")
            st.dataframe(table2, use_container_width=True)
        
        with col_t2:
            st.subheader("💰 Table 3: Monthly Metrics")
            st.dataframe(table3, use_container_width=True)
            
            # Additional metrics
            st.subheader("📊 Quick Stats")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("Total Sales", f"${table1['Sales'].sum():,}")
            
            with col_stat2:
                st.metric("Avg Salary", f"${table2['Salary'].mean():,.0f}")
            
            with col_stat3:
                st.metric("Latest Revenue", f"${table3['Revenue'].iloc[-1]:,}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem;'>
        Built with ❤️ using Streamlit | Data Dashboard v1.0
    </div>
    """, 
    unsafe_allow_html=True
)
