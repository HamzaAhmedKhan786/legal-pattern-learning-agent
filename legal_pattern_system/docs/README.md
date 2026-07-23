# Documentation Index

Use this folder as the project knowledge base.

## Main Architecture Docs

- [architecture.md](architecture.md): technical architecture, agents, data model,
  RBAC, LLM boundary, observability, and deployment shape.
- [system_design.md](system_design.md): presentation-ready system design with
  product, component, request, retrieval, validation, and learning diagrams.
- [application_flow.md](application_flow.md): page flow, workspace flow,
  generation sequence, feedback, admin, support, and export flow.
- [production_integration_guide.md](production_integration_guide.md): exact setup
  steps for SMTP, payments, Redis, MCP, hosting, classifier, law validation, and
  encryption key storage.
- [agent_security_sandboxing.md](agent_security_sandboxing.md): tool
  sandboxing, agent permissions, prompt-injection defense, jailbreak handling,
  and security tests.
- [document_classifier_training_data.md](document_classifier_training_data.md):
  how to connect the local `DocClassifier` project and where to source open
  legal data for classifier improvement.

## Assessment And Design Notes

- [additional_questions.md](additional_questions.md): answers to the three
  challenge questions.
- [design_decisions.md](design_decisions.md): major engineering and product
  tradeoffs.
- [feedback_postmortem.md](feedback_postmortem.md): what was missed in the first
  submission and how the design changed.
- [v2_agentic_corrections.md](v2_agentic_corrections.md): LLM-agentic corrections
  added after feedback.
- [qa_score_comparison.md](qa_score_comparison.md): how the QA score changed from
  0.9 to 1.0 and what the score means.

## Production Planning

- [production_backend_rag_plan.md](production_backend_rag_plan.md): database,
  RAG, official-source validation, model, and deployment plan.
- [production_deployment_subscription_mcp_solution.md](production_deployment_subscription_mcp_solution.md):
  subscription, data scale, model hosting, deployment, and MCP solution.
- [production_web_plan.md](production_web_plan.md): web app screens, backend
  services, frontend improvements, and data stores.

## Recommended Reading Order

1. Start with the root `README.md`.
2. Read `system_design.md` for the visual overview.
3. Read `application_flow.md` to understand how users move through the app.
4. Read `architecture.md` for technical depth.
5. Read `agent_security_sandboxing.md` before connecting tools or MCP servers.
6. Read `document_classifier_training_data.md` before retraining or wiring the
   external classifier.
7. Read `production_integration_guide.md` before deploying or connecting real
   services.
