from helper import load_env
load_env()
import streamlit as st
import os
from flow_pipeline import SalesPipeline
from crewai import Crew, Task, Process
from crewai.tasks.task_output import TaskOutput
from typing import Any, Dict
from crewai.agents.agent_builder.base_agent import BaseAgent

# Set OpenAI Model
os.environ['OPENAI_MODEL_NAME'] = 'gpt-4o-mini'

# Initialize the SalesPipeline
flow = SalesPipeline()

# Streamlit UI setup
st.title("💬 Lead Scoring and Engagement Dashboard") 

# Initialize the message log in session state if not already present
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Welcome! Click the button to run the pipeline."}]

# Define a custom handler to log interactions in real time
class CustomStreamlitHandler:
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def log_message(self, role: str, message: str) -> None:
        """Log the message into Streamlit's chat_message interface."""
        st.session_state.messages.append({"role": role, "content": message})
        st.chat_message(role).write(message)

# Create callback handlers for agent messages
manager_handler = CustomStreamlitHandler("Pipeline Manager")
scoring_agent_handler = CustomStreamlitHandler("Scoring Agent")
filtering_agent_handler = CustomStreamlitHandler("Filtering Agent")
email_agent_handler = CustomStreamlitHandler("Email Generator")

# Button to trigger the pipeline
if st.button("Run Pipeline"):
    with st.spinner("Running the pipeline..."):
        # Add a log message indicating pipeline start
        manager_handler.log_message("Pipeline Manager", "Starting the SalesPipeline...")

        # Execute the SalesPipeline
        crew_output = flow.kickoff()

        # Check if the output is a single CrewOutput or a list
        if isinstance(crew_output, list):
            all_task_outputs = [task for output in crew_output for task in output.tasks_output]
        else:
            all_task_outputs = crew_output.tasks_output

        # Process outputs dynamically as they are available
        for task_output in all_task_outputs:
            # Log agent interactions in the Task Outputs tab
            manager_handler.log_message("Pipeline Manager", f"Processing task: {task_output.description}")

            # Display agent conversations in the Task Outputs tab
            st.chat_message(task_output.agent).write(task_output.raw or "No conversation available.")

            # Check the type of task and log results to specific tabs
            if "lead scoring" in task_output.description.lower():
                scoring_agent_handler.log_message(
                    "Scoring Agent", 
                    f"Lead Scoring Task Completed: {task_output.raw}"
                )
            elif "lead filtering" in task_output.description.lower():
                filtering_agent_handler.log_message(
                    "Filtering Agent", 
                    f"Lead Filtering Task Completed: {task_output.raw}"
                )
            elif "email generation" in task_output.description.lower():
                email_agent_handler.log_message(
                    "Email Generator", 
                    f"Email Generation Task Completed: {task_output.raw}"
                )

        # Indicate pipeline completion
        manager_handler.log_message("Pipeline Manager", "Pipeline completed successfully!")
        st.success("Pipeline completed! Results are now available.")

# Display the messages in the UI
st.header("Pipeline Outputs")

# Tabs for various outputs
tab1, tab2, tab3, tab4 = st.tabs(["Task Outputs", "Lead Scores", "Filtered Leads", "Generated Emails"])

# Tab 1: Task Outputs
with tab1:
    st.write("Task Outputs (Agent Conversations):")
    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

# Tab 2: Lead Scores
with tab2:
    st.write("Lead Scores will be displayed here.")
    # Add logic for displaying structured lead scoring results

# Tab 3: Filtered Leads
with tab3:
    st.write("Filtered Leads will be displayed here.")
    # Add logic for displaying filtered leads

# Tab 4: Generated Emails
with tab4:
    st.write("Generated Emails will be displayed here.")
    # Add logic for displaying generated emails
