import streamlit as st
import json
from shillelagh.backends.apsw.db import connect


# Establish connection to Google Sheets
connection = connect(
    ":memory:",
    adapter_kwargs={
        "gsheetsapi": {"service_account_info": dict(st.secrets["gcp_service_account"])}
    },
)
sheetURL = st.secrets["private_gsheets_url"]

# Page 2 - Summary 3 - Llama
PAGE_NUM = 2

    
def init_session_state(num):
    if "ranking" not in st.session_state:
        st.session_state["ranking"] = 0

    if f'q{num}' not in st.session_state:
        st.session_state[f'q{num}'] = 0

    if f'eval{num}' not in st.session_state:
        st.session_state[f'eval{num}'] = {}


def show_question1():
    choices = [
        "1) No - critical details are left out that are necessary to understand the story",
        "2) Not really - it would be hard to appreciate the story from the details provided",
        "3) Mostly - covers the main points but small things missing",
        "4) Yes - the important details of the narrative are covered",
    ]

    index = 0
    if "coverage" in st.session_state[f"eval{PAGE_NUM}"]:
        # Restore saved answer if already entered
        index = int(st.session_state[f"eval{PAGE_NUM}"]["coverage"])-1
    st.session_state[f"eval{PAGE_NUM}"]["coverage"] = st.radio(
        "Does the summary cover the important plot points of the story?",
        options=choices,
        index=index
    )[:1]

    
def show_question2():
    choices = [
        "1) Yes - the summary includes incorrect details",
        "2) Somewhat - the summary misrepresents details",
        "3) Not really - mostly accurate but some details aren’t clear",
        "4) No - everything is correct in relation to the story",
    ]

    index=0
    if "faithfulness" in st.session_state[f"eval{PAGE_NUM}"]:
        # Restore saved answer if already entered
        index = int(st.session_state[f"eval{PAGE_NUM}"]["faithfulness"])-1
    st.session_state[f"eval{PAGE_NUM}"]["faithfulness"] = st.radio(
        "Does the summary misrepresent details from the story or make things up?",
        options=choices,
        index=index,
    )[:1]

    
def show_question3():
    choices = [
        "1) No - contains grammar errors or non sequiturs",
        "2) Not really - confusing to follow but fluent",
        "3) Mostly - a bit clunky but coherent and fluent",
        "4) Yes - easy to read and understand",
    ]

    index=0
    if "coherence" in st.session_state[f"eval{PAGE_NUM}"]:
        # Restore saved answer if already entered
        index = int(st.session_state[f"eval{PAGE_NUM}"]["coherence"])-1
    st.session_state[f"eval{PAGE_NUM}"]["coherence"] = st.radio(
        "Is the summary coherent, fluent and readable?",
        choices,
        index=index,
    )[:1]

    
def show_question4():
    choices = [
        "1) No - there is no analysis in the summary",
        "2) Not really - there is some analysis but it’s not correct",
        "3) Somewhat - there is some correct analysis but it’s not very thoughtful",
        "4) Yes - the summary touches on some of the themes/feelings/interpretation that you hoped to communicate as the writer",
    ]

    index=0
    if "interpretation" in st.session_state[f"eval{PAGE_NUM}"]:
        # Restore saved answer if already entered
        index = int(st.session_state[f"eval{PAGE_NUM}"]["interpretation"])-1
    st.session_state[f"eval{PAGE_NUM}"]["interpretation"] = st.radio(
        "Does the summary provide any correct analysis of some of the main takeaways or themes from the story?",
        choices,
        index=index,
    )[:1]

    
def show_responsequestion():
    value = ""
    if "feedback" in st.session_state[f"eval{PAGE_NUM}"]:
        # Restore saved answer if already entered
        value = st.session_state[f"eval{PAGE_NUM}"]["feedback"]
    st.session_state[f"eval{PAGE_NUM}"]["feedback"] = st.text_area(
        "Write a couple sentences (or more!) describing your general feelings on this summary and any feedback you have. What do you particularly like or not like?\nPlease make sure to press 'Command + Enter' to save your response before submitting.",
        value=value
    ).replace('"', "'")

   
def userid_entered(summaryID, title_text, summary_text):
    # Page Layout
    st.markdown("### Story Title")
    st.markdown(title_text)
    st.markdown("### Summary")
    st.markdown(summary_text)
    st.markdown("### Questions")

    # Display different questions depending on session state
    if st.session_state[f"q{PAGE_NUM}"] == 0:
        show_question1()
    elif st.session_state[f"q{PAGE_NUM}"] == 1:
        show_question2()
    elif st.session_state[f"q{PAGE_NUM}"] == 2:
        show_question3()
    elif st.session_state[f"q{PAGE_NUM}"] == 3:
        show_question4()
    elif st.session_state[f"q{PAGE_NUM}"] == 4:
        show_responsequestion()
    else:
        st.success(
            "You have answered all of the questions for this summary. Please select the next summary in the sidebar."
        )
    
    if st.session_state[f"q{PAGE_NUM}"] <= 4:
        # Position Back and Next/Submit buttons on left and right of page
        left, right = st.columns([0.9, 0.2])
        with left:
            # Back button returns to previous page
            st.button("Back", disabled=st.session_state[f"q{PAGE_NUM}"]==0, on_click=back_click)
        with right:
            if st.session_state[f"q{PAGE_NUM}"] < 4:
                # Next button moves on to next question
                st.button("Next", disabled=False, on_click=next_click)
            else:
                # Submit button submits answers
                st.button("Submit", disabled=False, on_click=submit_click)


def submit_click():
    # Submit answers to Google sheets
    insert = f"""
            INSERT INTO "{sheetURL}" (SummID, UserID, SourceText, SummText, Coverage, Faithfulness, Coherence, Interpretation, Feedback)
            VALUES ("{st.session_state[f"eval{PAGE_NUM}"]["summaryID"]}", "{st.session_state[f"eval{PAGE_NUM}"]["userID"]}", "{st.session_state[f"eval{PAGE_NUM}"]["title_text"]}", "{st.session_state[f"eval{PAGE_NUM}"]["summary_text"]}", "{st.session_state[f"eval{PAGE_NUM}"]["coverage"]}", "{st.session_state[f"eval{PAGE_NUM}"]["faithfulness"]}", "{st.session_state[f"eval{PAGE_NUM}"]["coherence"]}", "{st.session_state[f"eval{PAGE_NUM}"]["interpretation"]}", "{st.session_state[f"eval{PAGE_NUM}"]["feedback"]}" )
            """
    connection.execute(insert)
    st.session_state[f"q{PAGE_NUM}"] += 1
       
def next_click():
    # Update qestion number when next button is clicked
    st.session_state[f"q{PAGE_NUM}"] += 1
    
def back_click():
    # Update qestion number when back button is clicked
    st.session_state[f"q{PAGE_NUM}"] -= 1


if __name__ == "__main__":
    # Init the page
    st.markdown("### Instructions")
    guideline_name = "streamlit_interface/summary_page_instructions.txt"
    with open(guideline_name, "r") as f:
        guideline = f.read()
    st.markdown(guideline)

    # summaryID is none until the user enter's their ID
    summaryID = None
    init_session_state(num=str(PAGE_NUM))

    # select the next summary in the array of summaryIDs assigned to the user
    with open("streamlit_interface/user_summary_assignments.json", "r") as f:
        summaryIDs = json.load(f)
        if st.session_state["userID"] in summaryIDs:
            # Assumes summaries are ordered claude, gpt4, llama
            summaryID = summaryIDs[st.session_state["userID"]][PAGE_NUM]

    # pulling source and summary text from file
    with open("streamlit_interface/data/summaries.json", "r") as f:
        source_articles = json.load(f)
        # turn the list of jsons into a dictionary
        source_articles = {article["id"]: article for article in source_articles}

    # Don't show anything if the User ID isn't entered yet
    if not summaryID:
        st.error("Please enter your user ID on the home page")
    else:
        # Load the summary text
        title_text = source_articles[summaryID]["title"]
        summary_text = source_articles[summaryID]["summary"]
        
        # Initialize state
        st.session_state[f"eval{PAGE_NUM}"]["summaryID"] = summaryID
        st.session_state[f"eval{PAGE_NUM}"]["userID"] = st.session_state["userID"]
        st.session_state[f"eval{PAGE_NUM}"]["title_text"] = title_text
        st.session_state[f"eval{PAGE_NUM}"]["summary_text"] = summary_text.replace('"', "'")
        
        # Load the rest of the page
        userid_entered(summaryID, title_text, summary_text)
