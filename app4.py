from helper import load_env
load_env()
import streamlit as st
import os
from flow_pipeline import SalesPipeline
import pandas as pd
import textwrap
from IPython.display import HTML
from flow_pipeline import StreamToExpander
import sys
import textwrap

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
        "emails": []
    }


# Helper function: Add to chat history
def add_to_chat(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


# Function to parse pipeline outputs
def process_pipeline_outputs(emails):
    """Parse the outputs of tasks from the pipeline and update session state."""
    # Process lead scores
    scores = flow.state["score_crews_results"]
    if scores:
        for i in range(len(scores)):
            lead_scoring_result = scores[i].pydantic

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
            st.session_state.state["score_crews_results"].append(lead_data)

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
    #emails = flow.state["emails"]
    if emails:
        for email in emails:
            wrapped_email = textwrap.fill(email.raw, width=80)
            st.session_state.state["emails"].append(wrapped_email)


# Main pipeline execution
def kickoff_pipeline():
    with st.spinner("Running the pipeline..."):
        add_to_chat("assistant", "Starting the pipeline...")
        emails = flow.kickoff()
        process_pipeline_outputs(emails)
        add_to_chat("assistant", "Pipeline execution complete!")
    return emails 

# Streamlit UI components
st.title("Lead Scoring and Engagement Dashboard")

# Chat interface for pipeline execution
st.header("💬 SensAI Agents Interface",divider="green")
if st.button("Run Pipeline"):
    with st.status("🤖 **SenAI Agents at work...**", state="running", expanded=True) as status:
        with st.container(height=500, border=False):
            sys.stdout = StreamToExpander(st)
            result = kickoff_pipeline()
        status.update(label="✅ Email Campaign Ready!",
                        state="complete", expanded=False)

    # st.subheader("Personalised Email", anchor=False, divider="rainbow")

    # result_text = result[0].raw
    # wrapped_text = textwrap.fill(result_text, width=80)
    # st.markdown(wrapped_text)
    

# # Display previous chat messages
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])


# Tabs for parsed outputs
st.header("Pipeline Outputs")
tab1, tab2, tab3, tab4= st.tabs(
    ["Lead Scores", "Filtered Leads", "Generated Emails", "Costs"]
)

# Tab 1: Lead Scores
with tab1:
    st.write("Lead Scores:")
    if st.session_state.state["score_crews_results"]:
        for i in range(len(st.session_state.state["score_crews_results"])):
            lead_scores_df = pd.DataFrame.from_dict(
                st.session_state.state["score_crews_results"][i], orient="index", columns=["Value"]
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
        for index, email in enumerate(st.session_state.state["emails"]):
            scores = flow.state["score_crews_results"]
            lead_scoring_result = scores[index].pydantic
            st.text_area(f"Generated Email - {lead_scoring_result.company_info.company_name}", email, height=150)
    else:
        st.warning("No emails generated yet. Run the pipeline.")

# Tab 4: Costs
with tab4:
    st.write("Cost Analysis:")
    if flow.state.get("score_crews_results"):
        for index, email in enumerate(st.session_state.state["emails"]):
            lead_scoring_result = scores[index].pydantic
            # Convert UsageMetrics instance to a DataFrame
            df_usage_scoreLead_metrics = pd.DataFrame([flow.state["score_crews_results"][index].token_usage.dict()])
            # Convert UsageMetrics instance to a DataFrame
            df_usage_email_metrics = pd.DataFrame([result[index].token_usage.dict()])
            # Calculate total costs
            costs_score = 0.150 * df_usage_scoreLead_metrics['total_tokens'].sum() / 1_000_000
            costs_email = 0.150 * df_usage_email_metrics['total_tokens'].sum() / 1_000_000
            st.metric(label=f"Total Score Lead Costs - {lead_scoring_result.personal_info.name} - {lead_scoring_result.company_info.company_name} ($)", value=f"{costs_score:.4f}")
            st.table(df_usage_scoreLead_metrics)
            st.metric(label=f"Total Email Costs {lead_scoring_result.personal_info.name} - {lead_scoring_result.company_info.company_name} ($)", value=f"{costs_email:.4f}")
            st.table(df_usage_email_metrics)
    else:
        st.warning("No usage metrics available yet. Run the pipeline.")
