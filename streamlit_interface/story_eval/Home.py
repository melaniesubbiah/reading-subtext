import streamlit as st
import json



if __name__ == "__main__":
    # Initialize User ID
    if "userID" not in st.session_state:
        st.session_state["userID"] = ""

    # Load home page instructions
    st.markdown(
        "Please first enter your assigned user ID in the textbox. You will not be able to access the summaries without entering your ID."
    )
    with open("streamlit_interface/home_page_instructions.txt", "r") as f:
        instructions = f.read()
    st.markdown(instructions)

    # Load ID-summary pairings
    with open("streamlit_interface/user_summary_assignments.json", "r") as f:
        summaryIDs = json.load(f)
        if st.session_state["userID"] == "" or st.session_state["userID"] not in summaryIDs:
            st.session_state["userID"] = st.text_input("Enter your assigned user ID:")
        if st.session_state["userID"] in summaryIDs:
            summaryIDs = summaryIDs[st.session_state["userID"]]
            st.success('Thank you!')
