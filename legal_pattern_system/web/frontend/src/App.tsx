import React, { useState } from "react";

type AgentRun = {
  run_id: string;
  document_type: string;
  retrieval_coverage: number;
  initial_qa_score: number;
  final_qa_score: number;
  trace_dir: string;
};

export default function App() {
  const [result, setResult] = useState<AgentRun | null>(null);

  async function runDemo() {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_type: "dismissal_protection_suits",
        llm_provider: "mock",
        case_data: {
          case_no: "DPS-2024-999",
          court: "Labor Court Berlin",
          date_filed: "June 20, 2024",
          plaintiff_name: "Example Employee",
          plaintiff_address: "Example Street 1, 10115 Berlin, Germany",
          defendant_company: "Example Employer GmbH",
          defendant_address: "Employer Avenue 10, 10117 Berlin, Germany"
        }
      })
    });
    setResult(await response.json());
  }

  return (
    <main>
      <h1>Legal Pattern Learning Agent</h1>
      <button onClick={runDemo}>Run Demo Draft</button>
      {result && (
        <section>
          <h2>Run Result</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
