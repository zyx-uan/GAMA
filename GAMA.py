# Set up and run this Streamlit App
import streamlit as st
import pandas as pd
import json
from io import BytesIO
from helper_functions.utility import check_password  

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="GenAI Access Management Assistant (GAMA)"
)
# endregion <--------- Streamlit App Configuration --------->

 
# Check if the password is correct.  
if not check_password():  
    st.stop()

# Add disclaimer section
with st.expander("IMPORTANT NOTICE"):
    st.write("""
        This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

        Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

        Always consult with qualified professionals for accurate and personalized advice.
    """)

st.title("GenAI Access Management Assistant (GAMA)")

st.title("GenAI Access Management Assistant (GAMA)")

# Function for uploading files
def upload_excel_file(label, key):
    # Create a file uploader with a given label and key to upload Excel files
    uploaded_file = st.file_uploader(label, type=["xlsx"], key=key)
    if uploaded_file:
        try:
            # If key is "beacon_matrix", load all sheets; otherwise, load only the first sheet
            df = pd.read_excel(uploaded_file, sheet_name=None if key == "beacon_matrix" else 0)
            st.write(f"{label} loaded successfully!")
            if key != "beacon_matrix":
                st.dataframe(df)
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.write(f"Please upload {label}.")
    return None

output_attestation = None
access_attestation = upload_excel_file("RWD Attestation", "rwd_attestation")
access_matrix = upload_excel_file("BEACON Access Matrix", "beacon_matrix")
staff_list = upload_excel_file("Staff list", "staff_list")

# Processing the beacon matrix if it is uploaded
if access_matrix is not None:
  try:
    for team, df in access_matrix.items():
        # Set the 3rd row as the header, and convert the column names to uppercase
        df.columns = df.iloc[1].str.upper()
        df = df[2:].reset_index(drop=True)  # Skip the rows after the header row

        # Forward fill staff positions in the first column
        df.iloc[:, 0] = df.iloc[:, 0].ffill()

        # Drop rows where the 'ACCESS' column is NaN
        df = df[df["ACCESS"].notnull()]

        # Remove newline characters if any
        df['STAFF'] = df['STAFF'].str.replace(r'\n', '', regex=True)

        # Ensure that the roles are separated
        # e.g. Manager / Senior Manager will be split into rows with Manager and rows with Senior Manager with the other columns being the same

        df['STAFF'] = df['STAFF'].str.split(r'\s*/\s*')  # Split on '/', optionally surrounded by spaces
        df = df.explode('STAFF').reset_index(drop=True)

        access_matrix[team] = df
  except Exception as e:
    st.error("Please ensure that your BEACON Access Matrix file is in the correct layout.")

# Function to convert DataFrame to Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()


# Function to create a download button for DataFrame
def create_download_button(label, df, filename):
    file_data = to_excel(df)  # Convert DataFrame to Excel format
    st.download_button(
        label=label,
        data=file_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Function to highlight specific rows in a column
def highlight_rows(row, column_name, value):
    if row[column_name] == value:
        return ['background-color: #FFCCCB'] * len(row)
    else:
        return [''] * len(row)

# Processing attestation, access matrix, and staff list if all are uploaded
if access_attestation is not None and access_matrix is not None and staff_list is not None:
  try:

    # Creating a copy of the attestation file and filling 'Entitlement' column with empty string where NaN
    output_attestation = access_attestation.copy()
    output_attestation['Entitlement'] = output_attestation['Entitlement'].fillna('').astype(str)
    # Forward-fill 'Access' column for rows with "Group" type
    output_attestation["Access"] = output_attestation["Entitlement"].where(output_attestation["Type"] == "Group").ffill()
    # Merge attestation file with staff list to include staff details
    output_attestation['Login Name'] = output_attestation['Login Name'].str.upper()
    staff_list['Account Name'] = staff_list['Account Name'].str.upper()
    output_attestation = pd.merge(output_attestation, staff_list, left_on='Login Name', right_on='Account Name', how='left')

    # Function to check if access is correct
    def check_access(row, access_matrix):
        if pd.notna(row["Team"]):
            # Check if the row's "Team" is not null
            team_matrix = access_matrix.get(row["Team"])
            if team_matrix is not None:
                # Check if both 'Access' and 'Designation' match the records in team_matrix
                match = team_matrix[
                    (team_matrix.iloc[:, 1].str.strip().str.lower() == row["Access"].strip().lower()) &
                    (team_matrix.iloc[:, 0].str.strip().str.lower() == row["Designation"].strip().lower())
                ]
                return "Yes" if not match.empty else "No"
        return "No"

    # Apply the function to determine access correctness
    output_attestation["Correct to have access?"] = output_attestation.apply(
        lambda row: check_access(row, access_matrix), axis=1
    )

    # Ensure that rows that are not accesses, the value "Correct to have access?" is blank
    output_attestation.loc[output_attestation['Team'].isna() | (output_attestation['Team'] == ''), 'Correct to have access?'] = ''

    # Filter rows where access is incorrect
    access_not_have = output_attestation[output_attestation["Correct to have access?"] == "No"].reset_index(drop=True)

    # Highlight the wrong accesses in red
    output_attestation_highlighted = output_attestation.style.apply(highlight_rows, column_name="Correct to have access?", value="No", axis=1)

    # Create download buttons for output files
    create_download_button("Download Output File (All Accesses)", output_attestation_highlighted, "output_attestation.xlsx")
    create_download_button("Download Output File (Accesses that do not match)", access_not_have, "output_access_not_have.xlsx")

  except Exception as e:
    st.error("Error comparing all three files")
else:
  st.write("Please ensure the Excel files are in correct format.")



####################################################################### GENAI PORTION ############################################################################################################

from openai import OpenAI
client = OpenAI(
    api_key="sk-XEdjAX71x3GTVRBaN33d5Q",
    base_url="https://litellm.govtext.gov.sg/",
    default_headers={"user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0"},
)


# Define the function to get completion from ChatGPT
def get_completion_from_messages(messages, model="gpt-4o-prd-gcc2-lb", temperature=0, top_p=1.0, max_tokens=1000, n=1, json_output=False):
    if json_output == True:
      output_json_structure = {"type": "json_object"}
    else:
      output_json_structure = None

    response = client.chat.completions.create( #originally was openai.chat.completions
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=1,
        response_format=output_json_structure,
    )
    return response.choices[0].message.content





# Function to trigger ChatGPT to determine filter criteria or summary request
def triggerGAMA(user_message):
    # Prepare a dictionary of possible filter values for each relevant column in output_attestation
    filter_options = {col: list(output_attestation[col].unique()) for col in output_attestation.columns}

    # Create a formatted string of these options for inclusion in the system prompt
    filter_options_text = "\n".join([f'"{col}": {", ".join(map(str, values))}' for col, values in filter_options.items()])

    # System prompt to instruct AI to identify filters and summary requirements
    system_question = f"""\
    Read the incoming request, delimited by <incoming-message> tags, carefully. Based on the request, identify if the user is asking for:

    1. A summary of accesses (e.g., count of mismatches).
    2. Specific filters for Designation, Team, or other fields.

    If a summary is requested, indicate "summary_required": true and specify relevant fields. If filters are specified, include them under "filters".

    Return ONLY a JSON object in this format:
    {{
        "summary_required": true,
        "summary_type": "count_non_matching_accesses",
        "filters": [
            {{"filter_by": "Designation", "filter_value": "Manager"}},
            {{"filter_by": "Team", "filter_value": "Payout"}}
        ]
    }}

    Note:
    - The values for "filter_by" should match one of the following headers in the dataset: {list(output_attestation.columns)}.
    - The values for "filter_value" must be one of these:
    {filter_options_text}

    Ensure the response is strictly in JSON format without extra spaces or text outside the JSON object.
    """

    messages = [
        {'role': 'system', 'content': system_question},
        {'role': 'user', 'content': f"<incoming-message>{user_message}</incoming-message>"},
    ]

    response = get_completion_from_messages(messages)

    try:
        filter_info = json.loads(response)
    except json.JSONDecodeError:
        filter_info = {"summary_required": False, "filters": []}

    return filter_info


# Function to apply filters to the DataFrame based on ChatGPT's response
def apply_filters(output_attestation, filter_info):
    filtered_df = output_attestation
    for filter_item in filter_info.get("filters", []):
        filter_by = filter_item.get("filter_by")
        filter_value = filter_item.get("filter_value")

        if filter_by and filter_value:
            filtered_df = filtered_df[filtered_df[filter_by] == filter_value]
    return filtered_df

# Function to generate the summary based on the filtered data
def generate_summary(filtered_df, summary_type):
    if summary_type == "count_non_matching_accesses":
        count_non_matching = (filtered_df['Correct to have access?'] == 'No').sum()
        count_matching = (filtered_df['Correct to have access?'] == 'Yes').sum()
        return (f"Count of matching accesses: {count_matching}\n"
                f"Count of non-matching accesses: {count_non_matching}")
    else:
        return "Summary type not recognized."


# Streamlit user interface for input and output
if output_attestation is not None:
    user_message = st.text_input("Enter your query regarding the dataframe.")

    if st.button("Submit Prompt"):
        # Step 1: Get filtering and summary requirements from ChatGPT
        filter_info = triggerGAMA(user_message)

        # Construct the filter message so that users can confirm the filters
        if "filters" in filter_info:
            filter_message = "You have filtered the following:\n"
            for filter_item in filter_info["filters"]:
                filter_message += f"{filter_item['filter_by']}: {filter_item['filter_value']}\n"
        filter_message += "\nIf this is not your request, please try again."

        st.write(filter_message)

        # Step 2: Apply filters if specified
        filtered_data = apply_filters(output_attestation, filter_info)

        # Step 3: Check if summary is requested
        if filter_info.get("summary_required", False):
            summary_type = filter_info.get("summary_type", "")
            summary = generate_summary(filtered_data, summary_type)
            st.write("Summary of Accesses:")
            st.write(summary)
        else:
            # If no summary, display the filtered data
            create_download_button("Download Requested Accesses", filtered_data, "requested_data.xlsx")
