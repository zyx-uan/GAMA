import streamlit as st

st.title("About Us")

# Project Scope Section
st.header("Project Scope")
st.write("""
- Welcome to GenAI Access Management Assistant (GAMA). The application is developed to address the challenges in access management.
- GAMA will streamline the access management process by automating the access check in the Excel sheets.
- It will identify discrepancies in access rights across roles and departments.
""")

# Objectives Section
st.header("Objectives")
st.write("""
- The implementation of GAMA will reduce the manual workload for access management, freeing up valuable time for other strategic tasks.
- We estimate a typical review process with GAMA will take no more than 15 minutes per user, resulting in over 80% improvement in time spent.
- The AI-driven approach and ability to quickly identify and address access anomalies will minimize human errors in access management, thereby enhancing overall data security.
- GAMA will improve compliance with access management protocols through systematic approaches and comprehensive reporting.
""")

# Data Sources Section
st.header("Data Sources")
st.write("""
- Data are sourced internally, with access data populated by the Board's ITPM teams, and the list of staff generated from department organization charts.
- All data are classified up to Sensitive-Normal, with tokenization applied for the POC submission.
- Key Data Sources:
   - **RWD Attestation Excel**: Shows IT accesses that CPFB staff in the Retirement Withdrawal Department (RWD) currently have.
   - **BEACON Access Matrix Excel**: Shows accesses each CPFB staff should have based on their team and designation.
   - **Staff List Excel**: Shows the team and designation of each staff in RWD.
""")

# Features Section
st.header("Features")
st.write("""
1. Ensure that each staff member in RWD’s access aligns with the access matrix. Flag any unauthorized accesses and provide an output Excel file with matches/non-matches for download.
2. Determine if the user is requesting a count of access matches/non-matches and, if so, provide a tally.
3. Provide filtering options for the output Excel file based on specific data fields, with a downloadable Excel file based on user inputs.
""")