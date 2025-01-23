from helper import load_env
load_env()
import streamlit as st
import os
from flow_pipeline import SalesPipeline
import pandas as pd
import textwrap
import re
import sys

# Set OpenAI Model
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'

# Initialize the SalesPipeline
flow = SalesPipeline()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "state" not in st.session_state:
    st.session_state.state = {
        "score_crews_results": [],
        "filtered_leads": [],
        "emails": [],
        "task_outputs": []  # To store agent conversations and outputs
    }


# Helper class: StreamToExpander
class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'blue', 'orange']  # Define a list of colors
        self.color_index = 0  # Initialize color index

    def write(self, data):
        # Filter out ANSI escape codes
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

        # Highlight specific agent-related information
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace(
                "Entering new CrewAgentExecutor chain",
                f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]"
            )

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []

    def flush(self):
        pass  # Needed to implement the write() method for stdout redirection


# Helper function: Add to chat history
def add_to_chat(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


# Function to parse pipeline outputs
def process_pipeline_outputs(emails):
    """Parse the outputs of tasks from the pipeline and update session state."""
    scores = flow.state["score_crews_results"]
    if scores:
        lead_scoring_result = scores[0].pydantic

        # Prepare data for Lead Scores tab
        lead_data = {
            'Name': lead_scoring_result.personal_info.name,
            'Job Title': lead_scoring_result.personal_info.job_title,
            'Role Relevance': lead_scoring_result.personal_info.role_relevance,
            'Professional Background': lead_scoring_result.personal_info.professional_background,
            'Company Name': lead_scoring_result.company_info.company_name,
            'Industry': lead_scoring_result.company_info.industry,
            'Company Size': lead_scoring_result.company_info.company_size,
            'Revenue': lead_scoring_result.company_info.revenue,
            'Market Presence': lead_scoring_result.company_info.market_presence,
            'Lead Score': lead_scoring_result.lead_score.score,
            'Scoring Criteria': ', '.join(lead_scoring_result.lead_score.scoring_criteria),
            'Validation Notes': lead_scoring_result.lead_score.validation_notes
        }
        st.session_state.state["score_crews_results"] = lead_data

        # Process filtered leads
        filtered_leads_data = {
            'Name': lead_scoring_result.personal_info.name,
            'Job Title': lead_scoring_result.personal_info.job_title,
            'Role Relevance': lead_scoring_result.personal_info.role_relevance,
            'Professional Background': lead_scoring_result.personal_info.professional_background,
            'Company Name': lead_scoring_result.company_info.company_name,
            'Industry': lead_scoring_result.company_info.industry,
            'Validation Notes': lead_scoring_result.lead_score.validation_notes
        }
        st.session_state.state["filtered_leads"].append(filtered_leads_data)

    # Process emails
    if emails:
        for email in emails:
            wrapped_email = textwrap.fill(email.raw, width=80)
            st.session_state.state["emails"].append(wrapped_email)


# Main pipeline execution
def kickoff_pipeline():
    with st.spinner("Running the pipeline..."):
        add_to_chat("assistant", "Starting the pipeline...")
        # Create an expander for real-time streaming
        with st.expander("Agent Task Outputs", expanded=True) as expander:
            sys.stdout = StreamToExpander(expander)  # Redirect stdout to the expander
            emails = flow.kickoff()
            process_pipeline_outputs(emails)
        add_to_chat("assistant", "Pipeline execution complete!")
        sys.stdout = sys.__stdout__  # Reset stdout
    return emails


# Streamlit UI components
st.title("Lead Scoring and Engagement Dashboard")

# Chat interface for pipeline execution
st.header("💬 Chat Interface")
if st.button("Run Pipeline"):
    emails = kickoff_pipeline()

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Tabs for parsed outputs
st.header("Pipeline Outputs")
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Lead Scores", "Filtered Leads", "Generated Emails", "Costs", "Task Outputs"]
)

# Tab 1: Lead Scores
with tab1:
    st.write("Lead Scores:")
    if st.session_state.state["score_crews_results"]:
        lead_scores_df = pd.DataFrame.from_dict(
            st.session_state.state["score_crews_results"], orient="index", columns=["Value"]
        ).reset_index().rename(columns={"index": "Attribute"})
        st.table(lead_scores_df)
    else:
        st.warning("No scores available yet. Run the pipeline.")

# Tab 2: Filtered Leads
with tab2:
    st.write("Filtered Leads:")
    if st.session_state.state["filtered_leads"]:
        filtered_leads_df = pd.DataFrame(st.session_state.state["filtered_leads"])
        st.table(filtered_leads_df)
    else:
        st.warning("No filtered leads available yet. Run the pipeline.")

# Tab 3: Generated Emails
with tab3:
    st.write("Generated Emails:")
    if st.session_state.state["emails"]:
        for email in st.session_state.state["emails"]:
            st.text_area("Generated Email", email, height=150)
    else:
        st.warning("No emails generated yet. Run the pipeline.")

# Tab 4: Costs
with tab4:
    st.write("Cost Analysis:")
    if flow.state.get("score_crews_results"):
        usage_metrics_df = pd.DataFrame([flow.state["score_crews_results"][0].token_usage.dict()])
        cost = 0.150 * usage_metrics_df["total_tokens"].sum() / 1_000_000
        st.metric(label="Total Costs ($)", value=f"{cost:.4f}")
        st.table(usage_metrics_df)
    else:
        st.warning("No usage metrics available yet. Run the pipeline.")

# Tab 5: Task Outputs
with tab5:
    st.write("Task Outputs (Agent Conversations):")
    if st.session_state["task_outputs"]:
        for output in st.session_state["task_outputs"]:
            with st.expander(f"Agent: {output['agent']}", expanded=False):
                st.write(f"**Task Description:** {output['description']}")
                st.text_area("Conversation", output["conversation"], height=200)
    else:
        st.warning("No task outputs available yet. Run the pipeline.")
