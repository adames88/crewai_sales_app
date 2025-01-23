import pandas as pd





def fetch_leads(path):
    # Specify the path to your Excel file
    excel_file_path = path

    # Read the Excel file
    try:
        leads_df = pd.read_csv(excel_file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Excel file not found at {excel_file_path}. Please check the path.")
    
    # Convert the DataFrame to the required format
    leads = []
    for _, row in leads_df.iterrows():
        lead = {
            "lead_data": {
                "name": row["name"],
                "job_title": row["job_title"],
                "company": row["company"],
                "email": row["email"],
                "use_case": row["usecase"]
            },
        }
        leads.append(lead)
    
    return leads


if __name__=="__main__":
    path = "./sales_leads.csv"
    print(fetch_leads(path))