from helper import load_env
load_env()
import streamlit as st
import os
from flow_pipeline import SalesPipeline
import pandas as pd

# Set OpenAI Model
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'

# Initialize the SalesPipeline
flow = SalesPipeline()

# Initialize global state for Streamlit
if "state" not in st.session_state:
    st.session_state.state = {
        "task_outputs": {},  # Task outputs from the crew
        "score_crews_results": [],  # Scoring results
        "stored_scores": [],  # Saved scores (database-like)
        "filtered_leads": [],  # Filtered leads
        "emails": []  # Generated emails
    }

# Function to run the pipeline
def kickoff_pipeline():
    with st.spinner("Running the pipeline..."):
        # Execute the SalesPipeline (Crew execution)
        crew_output = flow.kickoff()

        # Handle both single CrewOutput and list of CrewOutput objects
        if isinstance(crew_output, list):  # Multiple outputs (e.g., kickoff_for_each)
            all_task_outputs = []
            for single_output in crew_output:
                all_task_outputs.extend(single_output.tasks_output)
        else:  # Single output (kickoff())
            all_task_outputs = crew_output.tasks_output

        # Store structured results in Streamlit state
        st.session_state.state["score_crews_results"] = [
            output.pydantic.to_dict() if output.pydantic else output.raw for output in all_task_outputs
        ]
        st.session_state.state["stored_scores"] = flow.state.get("stored_scores", [])
        st.session_state.state["filtered_leads"] = flow.state.get("filtered_leads", [])
        st.session_state.state["emails"] = flow.state.get("emails", [])

        st.success("Pipeline completed! Results are now available.")

# Streamlit UI components
st.title("Lead Scoring and Engagement Dashboard")

# Button to trigger the pipeline
if st.button("Run Pipeline"):
    kickoff_pipeline()

st.header("Pipeline Outputs")

# Tabs for Lead Scores, Filtered Leads, Emails, and Detailed Task Outputs
tab1, tab2, tab3, tab4 = st.tabs(["Lead Scores", "Filtered Leads", "Generated Emails", "Task Outputs"])

# Tab 1: Lead Scores
with tab1:
    st.write("Lead Scores:")
    if st.session_state.state["score_crews_results"]:
        # Extract scores from structured outputs if possible
        score_results = []
        for result in st.session_state.state["score_crews_results"]:
            if isinstance(result, dict):  # Structured data (expected format)
                score_results.append({
                    "Lead Name": result.get("personal_info", {}).get("name", "N/A"),
                    "Job Title": result.get("personal_info", {}).get("job_title", "N/A"),
                    "Company Name": result.get("company_info", {}).get("company_name", "N/A"),
                    "Lead Score": result.get("lead_score", {}).get("score", "N/A"),
                })
            elif isinstance(result, str):  # Raw string fallback
                score_results.append({"Raw Output": result})
            else:
                st.warning(f"Unexpected data type in score results: {type(result)}")

        # Convert to DataFrame and display
        if score_results:
            scores_df = pd.DataFrame(score_results)
            st.table(scores_df)
        else:
            st.warning("No valid scores available yet. Run the pipeline.")
    else:
        st.warning("No scores available yet. Run the pipeline.")

# Tab 2: Filtered Leads
with tab2:
    st.write("Filtered Leads:")
    if st.session_state.state["filtered_leads"]:
        filtered_leads_df = pd.DataFrame([
            {
                "Lead Name": lead["personal_info"]["name"],
                "Job Title": lead["personal_info"]["job_title"],
                "Company Name": lead["company_info"]["company_name"],
                "Lead Score": lead["lead_score"]["score"]
            }
            for lead in st.session_state.state["filtered_leads"]
        ])
        st.table(filtered_leads_df)
    else:
        st.warning("No filtered leads available yet. Run the pipeline.")

# Tab 3: Generated Emails
with tab3:
    st.write("Generated Emails:")
    if st.session_state.state["emails"]:
        emails_df = pd.DataFrame(st.session_state.state["emails"])
        st.table(emails_df)
    else:
        st.warning("No emails generated yet. Run the pipeline.")

# Tab 4: Task Outputs
with tab4:
    st.write("Task Outputs:")
    if st.session_state.state["score_crews_results"]:
        task_outputs = st.session_state.state["score_crews_results"]
        st.json(task_outputs)  # For detailed JSON viewing
    else:
        st.warning("No task outputs available yet. Run the pipeline.")
