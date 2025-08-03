import v3_final_advanced_retrieval as retrieval_module

# === Customized List of 20 Questions Based on Your Dataset ===
questions = [
    # 🎯 Specific Scheme Queries
    "What benefits are offered by the National Mission on Edible Oils - Oil Palm?",
    "How can I apply for the Tripura Industrial Investment Promotion Incentive scheme?",
    "Who is eligible under the Fee Waiver Scheme for SC/ST Students in Gujarat?",
    "Explain the assistance provided by the Mukhyamantri Kanya Vivah Yojana.",
    "What is the objective of the Chai Vikas Yojana for tea farmers?",

    # ⚙️ Process & Application Queries
    "What is the step-by-step process to apply for financial aid under the Widow Pension Scheme of West Bengal?",
    "How do I register for the Maternity Benefit Scheme in Andhra Pradesh?",
    "Can I apply online for the Skill Development Allowance in Himachal Pradesh?",
    "What documents are required for the Housing Subsidy Scheme for SC families?",
    "How to avail subsidy under the Credit Linked Subsidy Scheme for MIG category?",

    # 👥 Beneficiary-Focused Queries
    "Are there any government schemes supporting artisans in Kerala?",
    "Is there financial assistance for differently-abled persons in Puducherry?",
    "Are there any marriage assistance schemes for daughters of widows in Delhi?",
    "What schemes support farmers adopting natural farming practices?",
    "Which schemes provide educational support to children of construction workers?",

    # 📄 General & Category Queries
    "List government schemes promoting renewable energy adoption.",
    "What schemes provide financial help for small-scale industries in Tripura?",
    "Are there any pension schemes available for senior citizens in Dadra & Nagar Haveli?",
    "Which government schemes help unemployed youth start businesses in Tamil Nadu?",
    "Tell me about welfare schemes for building and construction workers in Delhi."
]

# === Run Retrieval & Save Results ===
output_file = "retrieval_test_results.txt"

with open(output_file, "w", encoding="utf-8") as f:
    for idx, question in enumerate(questions, 1):
        f.write(f"🟢 Question {idx}: {question}\n\n")
        context = retrieval_module.retrieve_context(question)
        f.write(f"{context}\n")
        f.write("\n" + "="*100 + "\n\n")

print(f"✅ Automated testing complete! Results saved to '{output_file}'")
