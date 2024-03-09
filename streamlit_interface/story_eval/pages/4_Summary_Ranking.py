import streamlit as st
import json
from shillelagh.backends.apsw.db import connect


# Establish Google sheets connection
connection = connect(
    ":memory:",
    adapter_kwargs={
        "gsheetsapi": {"service_account_info": dict(st.secrets["gcp_service_account"])}
    },
)

sheetURL = st.secrets["private_gsheets_url"]


def submit_click():
    # Submit answers to Google sheets
    insert = f"""
            INSERT INTO "{sheetURL}" (UserID, Preference)
            VALUES ("{st.session_state["evalranking"]["userID"]}", "{st.session_state["evalranking"]["preference"]}" )
            """
    connection.execute(insert)
    st.session_state[f"qranking"] += 1
    
    
def ranking_question(title, summaries):
    # Page layout
    st.markdown("### Story Title")
    st.markdown(title)
    st.markdown("### Summary 1")
    st.markdown(summaries[0])
    st.markdown("### Summary 2")
    st.markdown(summaries[1])
    st.markdown("### Summary 3")
    st.markdown(summaries[2])
    st.markdown("### Ranking")

    # Ranking question
    st.session_state["evalranking"]["userID"] = st.session_state["userID"]
    st.session_state["evalranking"]["preference"] = {}

    choices = ["Summary 1", "Summary 2", "Summary 3"]
    st.session_state["evalranking"]["preference"]["1"] = st.selectbox(
        "1st", options=choices
    )
    st.session_state["evalranking"]["preference"]["2"] = st.selectbox(
        "2nd", options=choices
    )
    st.session_state["evalranking"]["preference"]["3"] = st.selectbox(
        "3rd", options=choices
    )
    
    # Submit button to save answers
    st.button("Submit", disabled=False, on_click=submit_click)


if __name__ == "__main__":
    # TODO load info for this from file so don't have to do the other questions first
    
    # Init the page
    st.markdown("### Instructions")
    st.markdown("Rank the summaries in your order of preference. Place the one that seems the best in position 1 and the worst in position 3.")

    # Session state initialization
    if "qranking" not in st.session_state:
        st.session_state["qranking"] = 0
    if "evalranking" not in st.session_state:
        st.session_state["evalranking"] = {}
        
    # Load summary assignments
    with open("streamlit_interface/user_summary_assignments.json", "r") as f:
        assignments = json.load(f)

    if not st.session_state["userID"] or st.session_state["userID"] not in assignments:
        st.error("Please enter your user ID on the home page")
    elif st.session_state["qranking"] < 1:
        # Assumes summaries are ordered claude, gpt4, llama
        summaryIDs = assignments[st.session_state["userID"]]

        # pulling source and summary text from file
        with open("streamlit_interface/data/summaries.json", "r") as f:
            source_articles = json.load(f)
            # turn the list of jsons into a dictionary
            source_articles = {article["id"]: article for article in source_articles}
        
        title = source_articles[summaryIDs[0]]["title"]
        summaries = [source_articles[i]['summary'] for i in summaryIDs]
        ranking_question(title, summaries)
    else:
        st.success(
            "You have answered the ranking question."
        )
