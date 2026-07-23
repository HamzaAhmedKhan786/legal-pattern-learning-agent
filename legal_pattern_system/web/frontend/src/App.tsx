import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
import "./App.css";

type AgentStep = {
  name: string;
  purpose: string;
  input_summary: string;
  output_summary: string;
  artifact_path: string;
};

type AgentRun = {
  run_id: string;
  document_type: string;
  steps: AgentStep[];
  retrieval_coverage: number;
  initial_qa_score: number;
  final_qa_score: number;
  trace_dir: string;
  draft_markdown?: string;
  execution_log?: ExecutionLogEvent[];
  legal_validation?: {
    country: string;
    status: string;
    detected_citations: string[];
    allowed_official_domains: string[];
    official_source_hosts_seen: string[];
    instruction: string;
  };
  human_review?: {
    status?: string;
    review_required?: boolean;
    qa_score?: number;
    review_reasons?: string[];
  };
};

type ExecutionLogEvent = {
  timestamp?: string;
  agent: string;
  phase: string;
  status: "queued" | "running" | "completed" | "blocked" | "failed" | string;
  message: string;
  details?: Record<string, unknown>;
};

type SourceDocument = {
  id: number;
  name: string;
  content: string;
};

type FieldDef = {
  key: string;
  label: string;
  required?: boolean;
  type?: "text" | "date" | "select" | "money";
  options?: string[];
};

type UserAccount = {
  id?: string;
  firm_id?: string;
  name: string;
  email: string;
  accountType: "individual" | "firm";
  role: "senior_lawyer" | "junior_lawyer" | "paralegal";
  email_verified?: boolean;
};

type ProviderSettings = {
  provider: string;
  model: string;
  apiKey: string;
  baseUrl: string;
  legalCountry: string;
  outputLanguage: AppLanguage;
};

type LegalVerificationResult = {
  country: string;
  verification_status: string;
  allowed_domains: string[];
  checked_sources: Array<{ url: string; official: boolean }>;
  rejected_sources: Array<{ url: string; official: boolean }>;
  instruction: string;
};

type FeedbackRecord = {
  id: string;
  created_at: string;
  run_id: string;
  sentiment: "positive" | "negative";
  comment: string;
  document_type: string;
  draft_markdown: string;
  case_data: Record<string, string>;
  qa_score?: number;
  reviewer: string;
};

type SamplePack = {
  id: string;
  label: string;
  backendDocType: string;
  description: string;
  caseData: Record<string, string>;
  sourceDocuments?: SourceDocument[];
};

type ClassificationResult = {
  index?: number;
  classifier?: string;
  status: string;
  filename?: string;
  raw_label?: string;
  practice_area?: string;
  document_type?: string;
  topic?: string;
  pack_id?: string;
  confidence?: number;
  signals?: string[];
  security?: unknown;
};

type ClassifierCoverage = {
  platform_catalog_types: number;
  external_classifier_labels: number;
  direct_platform_mappings: number;
  note: string;
};

type Page = "workspace" | "login" | "signup" | "library" | "classifier" | "history" | "profile" | "settings" | "admin" | "contact" | "about" | "careers" | "privacy" | "terms" | "impressum" | "gdpr";
type ThemeMode = "system" | "light" | "dark";
type AppLanguage = "DE" | "EN" | "ES" | "FR" | "IT";

const appLanguages: Array<{ code: AppLanguage; flagSrc: string; label: string; shortLabel: string }> = [
  { code: "DE", flagSrc: "/flags/de.svg", label: "Deutsch", shortLabel: "DE" },
  { code: "EN", flagSrc: "/flags/gb.svg", label: "English", shortLabel: "EN" },
  { code: "ES", flagSrc: "/flags/es.svg", label: "Spanish", shortLabel: "ES" },
  { code: "FR", flagSrc: "/flags/fr.svg", label: "French", shortLabel: "FR" },
  { code: "IT", flagSrc: "/flags/it.svg", label: "Italian", shortLabel: "IT" }
];

const uiCopy: Record<AppLanguage, Record<string, string>> = {
  EN: {
    workspace: "Workspace",
    samples: "Samples",
    classifier: "Classifier",
    history: "History",
    settings: "Settings",
    admin: "Admin",
    about: "About",
    contact: "Contact",
    careers: "Careers",
    privacy: "Privacy",
    terms: "Terms",
    impressum: "Impressum",
    gdpr: "GDPR",
    signOut: "Sign out",
    login: "Log in",
    signup: "Sign up",
    provider: "Provider",
    workspaceEyebrow: "Firm legal drafting workspace",
    workspaceTitle: "Legal AI Pattern Drafting Studio",
    workspaceSubtitle: "Learn from approved examples, draft from new facts, and route every result to lawyer review.",
    sourceLearning: "Source Learning",
    runnableSample: "Runnable sample",
    customRoadmap: "Custom / roadmap",
    practiceArea: "Practice area",
    documentType: "Document type",
    taxonomyNote: "The second dropdown is filtered by the selected practice area. Implemented prototype topics open a runnable sample pack; the remaining topics are shown as the scalable document taxonomy.",
    builtInSamples: "Built-in samples",
    mySamples: "My samples",
    builtInPack: "Built-in sample pack",
    newCaseFacts: "New Case Facts",
    requiredComplete: "required complete",
    factsNote: "Prototype fact schema for the selected runnable document family. Uploads can prefill these fields from JSON or simple key-value intake notes.",
    uploadIntake: "Upload intake JSON or key-value text",
    readyForDrafting: "Ready for drafting",
    emptyTitle: "Build a firm-specific draft from precedent examples and structured case facts.",
    emptyText: "Select an approved sample pack or provide your own examples. Required facts are collected in structured fields, optional facts can be uploaded from intake files, and every generated document is routed to review.",
    lawyerReviewRequired: "Prototype: lawyer review required before use"
  },
  DE: {
    workspace: "Arbeitsbereich",
    samples: "Beispiele",
    classifier: "Klassifizierer",
    history: "Verlauf",
    settings: "Einstellungen",
    admin: "Admin",
    about: "Uber uns",
    contact: "Kontakt",
    careers: "Karriere",
    privacy: "Datenschutz",
    terms: "Bedingungen",
    impressum: "Impressum",
    gdpr: "DSGVO",
    signOut: "Abmelden",
    login: "Anmelden",
    signup: "Registrieren",
    provider: "Anbieter",
    workspaceEyebrow: "Kanzlei-Arbeitsbereich fur juristische Entwurfe",
    workspaceTitle: "Legal AI Pattern Drafting Studio",
    workspaceSubtitle: "Aus freigegebenen Beispielen lernen, aus neuen Fakten entwerfen und jedes Ergebnis zur anwaltlichen Prufung leiten.",
    sourceLearning: "Quellenlernen",
    runnableSample: "Ausfuhrbares Beispiel",
    customRoadmap: "Eigene Daten / Roadmap",
    practiceArea: "Rechtsgebiet",
    documentType: "Dokumenttyp",
    taxonomyNote: "Die zweite Auswahlliste wird nach dem Rechtsgebiet gefiltert. Implementierte Prototyp-Themen offnen ein ausfuhrbares Beispielpaket; weitere Themen zeigen die skalierbare Dokumenttaxonomie.",
    builtInSamples: "Integrierte Beispiele",
    mySamples: "Meine Beispiele",
    builtInPack: "Integriertes Beispielpaket",
    newCaseFacts: "Neue Falldaten",
    requiredComplete: "Pflichtfelder vollstandig",
    factsNote: "Prototypisches Faktenschema fur die ausgewahlte Dokumentfamilie. Uploads konnen Felder aus JSON oder einfachen Schlussel-Wert-Notizen vorbefullen.",
    uploadIntake: "Intake als JSON oder Schlussel-Wert-Text hochladen",
    readyForDrafting: "Bereit zum Entwerfen",
    emptyTitle: "Erstellen Sie einen kanzleispezifischen Entwurf aus Praxismustern und strukturierten Falldaten.",
    emptyText: "Wahlen Sie ein freigegebenes Beispielpaket oder eigene Beispiele. Pflichtfelder werden strukturiert erfasst, optionale Fakten konnen aus Intake-Dateien hochgeladen werden, und jeder Entwurf geht in die Prufung.",
    lawyerReviewRequired: "Prototyp: anwaltliche Prufung erforderlich"
  },
  ES: {
    workspace: "Espacio",
    samples: "Muestras",
    classifier: "Clasificador",
    history: "Historial",
    settings: "Ajustes",
    admin: "Admin",
    about: "Acerca",
    contact: "Contacto",
    careers: "Carreras",
    privacy: "Privacidad",
    terms: "Terminos",
    impressum: "Aviso legal",
    gdpr: "GDPR",
    signOut: "Salir",
    login: "Entrar",
    signup: "Registro",
    provider: "Proveedor",
    workspaceEyebrow: "Espacio de redaccion legal del despacho",
    workspaceTitle: "Legal AI Pattern Drafting Studio",
    workspaceSubtitle: "Aprende de ejemplos aprobados, redacta desde nuevos hechos y envia cada resultado a revision legal.",
    sourceLearning: "Aprendizaje de fuentes",
    runnableSample: "Muestra ejecutable",
    customRoadmap: "Personalizado / roadmap",
    practiceArea: "Area legal",
    documentType: "Tipo de documento",
    taxonomyNote: "El segundo desplegable se filtra por area legal. Los temas implementados abren un paquete ejecutable; los demas muestran la taxonomia escalable.",
    builtInSamples: "Muestras incluidas",
    mySamples: "Mis muestras",
    builtInPack: "Paquete incluido",
    newCaseFacts: "Nuevos hechos del caso",
    requiredComplete: "obligatorio completo",
    factsNote: "Esquema de hechos del prototipo para la familia documental seleccionada. Los archivos pueden rellenar campos desde JSON o texto clave-valor.",
    uploadIntake: "Subir intake JSON o texto clave-valor",
    readyForDrafting: "Listo para redactar",
    emptyTitle: "Crea un borrador especifico del despacho desde precedentes y hechos estructurados.",
    emptyText: "Selecciona un paquete aprobado o proporciona ejemplos propios. Los hechos requeridos se recogen en campos estructurados y cada documento generado pasa a revision.",
    lawyerReviewRequired: "Prototipo: revision legal requerida"
  },
  FR: {
    workspace: "Espace",
    samples: "Exemples",
    classifier: "Classificateur",
    history: "Historique",
    settings: "Reglages",
    admin: "Admin",
    about: "A propos",
    contact: "Contact",
    careers: "Carrieres",
    privacy: "Confidentialite",
    terms: "Conditions",
    impressum: "Mentions",
    gdpr: "RGPD",
    signOut: "Deconnexion",
    login: "Connexion",
    signup: "Inscription",
    provider: "Fournisseur",
    workspaceEyebrow: "Espace de redaction juridique du cabinet",
    workspaceTitle: "Legal AI Pattern Drafting Studio",
    workspaceSubtitle: "Apprendre a partir d'exemples approuves, rediger depuis de nouveaux faits et envoyer chaque resultat en revue juridique.",
    sourceLearning: "Apprentissage des sources",
    runnableSample: "Exemple executable",
    customRoadmap: "Personnalise / feuille de route",
    practiceArea: "Domaine juridique",
    documentType: "Type de document",
    taxonomyNote: "Le second menu est filtre par domaine juridique. Les sujets implementes ouvrent un paquet executable; les autres affichent la taxonomie extensible.",
    builtInSamples: "Exemples integres",
    mySamples: "Mes exemples",
    builtInPack: "Paquet integre",
    newCaseFacts: "Nouveaux faits",
    requiredComplete: "obligatoire complete",
    factsNote: "Schema de faits prototype pour la famille documentaire selectionnee. Les fichiers peuvent pre-remplir les champs depuis JSON ou texte cle-valeur.",
    uploadIntake: "Importer JSON ou texte cle-valeur",
    readyForDrafting: "Pret a rediger",
    emptyTitle: "Creez un brouillon propre au cabinet a partir de precedents et de faits structures.",
    emptyText: "Selectionnez un paquet approuve ou fournissez vos propres exemples. Les faits requis sont collectes dans des champs structures et chaque document est soumis a revue.",
    lawyerReviewRequired: "Prototype : revue juridique requise"
  },
  IT: {
    workspace: "Workspace",
    samples: "Esempi",
    classifier: "Classificatore",
    history: "Cronologia",
    settings: "Impostazioni",
    admin: "Admin",
    about: "Chi siamo",
    contact: "Contatto",
    careers: "Carriere",
    privacy: "Privacy",
    terms: "Termini",
    impressum: "Note legali",
    gdpr: "GDPR",
    signOut: "Esci",
    login: "Accedi",
    signup: "Registrati",
    provider: "Provider",
    workspaceEyebrow: "Workspace dello studio per redazione legale",
    workspaceTitle: "Legal AI Pattern Drafting Studio",
    workspaceSubtitle: "Impara da esempi approvati, redigi da nuovi fatti e invia ogni risultato alla revisione legale.",
    sourceLearning: "Apprendimento fonti",
    runnableSample: "Esempio eseguibile",
    customRoadmap: "Personalizzato / roadmap",
    practiceArea: "Area legale",
    documentType: "Tipo documento",
    taxonomyNote: "Il secondo menu e filtrato per area legale. I temi implementati aprono un pacchetto eseguibile; gli altri mostrano la tassonomia scalabile.",
    builtInSamples: "Esempi inclusi",
    mySamples: "I miei esempi",
    builtInPack: "Pacchetto incluso",
    newCaseFacts: "Nuovi fatti del caso",
    requiredComplete: "obbligatorio completo",
    factsNote: "Schema fatti prototipo per la famiglia documentale selezionata. I file possono compilare i campi da JSON o testo chiave-valore.",
    uploadIntake: "Carica intake JSON o testo chiave-valore",
    readyForDrafting: "Pronto per redigere",
    emptyTitle: "Crea una bozza specifica dello studio da precedenti e fatti strutturati.",
    emptyText: "Seleziona un pacchetto approvato o fornisci esempi propri. I fatti richiesti sono raccolti in campi strutturati e ogni documento generato va in revisione.",
    lawyerReviewRequired: "Prototipo: revisione legale richiesta"
  }
};

const dismissalFields: FieldDef[] = [
  { key: "case_no", label: "Case number", required: true },
  { key: "court", label: "Court", required: true, type: "select", options: ["Labor Court Berlin", "Labor Court Hamburg", "Labor Court Munich", "Labor Court Frankfurt"] },
  { key: "date_filed", label: "Date filed", required: true },
  { key: "plaintiff_name", label: "Plaintiff name", required: true },
  { key: "plaintiff_address", label: "Plaintiff address", required: true },
  { key: "plaintiff_employee_id", label: "Employee ID" },
  { key: "plaintiff_position", label: "Position", required: true, type: "select", options: ["Senior Product Manager", "Engineering Manager", "Research Scientist", "Quality Manager", "Sales Director"] },
  { key: "plaintiff_department", label: "Department", type: "select", options: ["Product", "Engineering", "Research", "Quality", "Sales", "Operations"] },
  { key: "plaintiff_hire_date", label: "Hire date", required: true },
  { key: "defendant_company", label: "Defendant company", required: true },
  { key: "defendant_address", label: "Defendant address", required: true },
  { key: "defendant_legal_representative", label: "Defendant representative" },
  { key: "defendant_hr_contact", label: "HR contact" }
];

const damagesFields: FieldDef[] = [
  { key: "case_no", label: "Case number", required: true },
  { key: "court", label: "Court", required: true, type: "select", options: ["District Court Berlin", "Regional Court Berlin", "District Court Hamburg", "Regional Court Munich"] },
  { key: "date_filed", label: "Date filed", required: true },
  { key: "plaintiff_name", label: "Plaintiff name", required: true },
  { key: "plaintiff_address", label: "Plaintiff address", required: true },
  { key: "plaintiff_legal_representative", label: "Plaintiff representative" },
  { key: "plaintiff_registration", label: "Plaintiff registration" },
  { key: "defendant_name", label: "Defendant name", required: true },
  { key: "defendant_address", label: "Defendant address", required: true },
  { key: "defendant_legal_representative", label: "Defendant representative" },
  { key: "defendant_registration", label: "Defendant registration" },
  { key: "total_damages", label: "Total damages", required: true, type: "money" }
];

const customFields: FieldDef[] = [
  { key: "case_no", label: "Matter or case number", required: true },
  { key: "court", label: "Court or forum", required: true },
  { key: "date_filed", label: "Draft date", required: true },
  { key: "plaintiff_name", label: "Client / claimant", required: true },
  { key: "plaintiff_address", label: "Client address" },
  { key: "defendant_name", label: "Opposing party", required: true },
  { key: "defendant_address", label: "Opposing party address" },
  { key: "matter_summary", label: "Matter summary", required: true },
  { key: "requested_relief", label: "Requested relief" }
];

const dismissalCaseData = {
  case_no: "DPS-2024-999",
  court: "Labor Court Berlin",
  date_filed: "June 20, 2024",
  plaintiff_name: "Example Employee",
  plaintiff_address: "Example Street 1, 10115 Berlin, Germany",
  plaintiff_employee_id: "EMP-2024-0999",
  plaintiff_position: "Senior Product Manager",
  plaintiff_department: "Product",
  plaintiff_hire_date: "May 1, 2020",
  defendant_company: "Example Employer GmbH",
  defendant_address: "Employer Avenue 10, 10117 Berlin, Germany",
  defendant_legal_representative: "Dr. Example Counsel",
  defendant_hr_contact: "Example HR Director"
};

const damagesCaseData = {
  case_no: "CFD-2024-999",
  court: "District Court Berlin",
  date_filed: "June 20, 2024",
  plaintiff_name: "Example Claimant GmbH",
  plaintiff_address: "Example Street 2, 10115 Berlin, Germany",
  plaintiff_legal_representative: "CEO Example Representative",
  plaintiff_registration: "HRB 99999 B, Amtsgericht Berlin-Charlottenburg",
  defendant_name: "Example Defendant AG",
  defendant_address: "Defendant Avenue 20, 10117 Berlin, Germany",
  defendant_legal_representative: "Board of Directors",
  defendant_registration: "HRB 88888 B, Amtsgericht Berlin-Charlottenburg",
  total_damages: "EUR 325,000"
};

const starterSourceDocuments: SourceDocument[] = [
  {
    id: 1,
    name: "dismissal_firm_sample_1.md",
    content: `# DISMISSAL PROTECTION SUIT

**Case No.:** DPS-2024-101
**Court:** Labor Court Berlin
**Date Filed:** March 4, 2024

## PLAINTIFF
**Name:** Maria Schneider
**Address:** Old Sample Address 1
**Employee ID:** EMP-101
**Position:** Product Lead
**Department:** Product
**Hire Date:** January 10, 2019

## DEFENDANT
**Company:** Sample Employer GmbH
**Address:** Old Employer Address
**Legal Representative:** Dr. Sample Counsel
**HR Contact:** Sample HR Lead

## STATEMENT OF CLAIM
The Plaintiff contests the dismissal and requests protection under applicable employment law.

## I. FACTUAL BACKGROUND
The Plaintiff was employed in a senior product role. The termination followed a restructuring notice.

## II. LEGAL GROUNDS
The dismissal lacks urgent operational necessity under Section 1 KSchG. Social selection under Section 1 Abs. 3 KSchG was not properly applied. Consultation under Section 102 BetrVG should be reviewed.

## III. RELIEF SOUGHT
The Plaintiff requests reinstatement or appropriate relief.

## SUPPORTING EVIDENCE
Employment contract, dismissal notice, HR correspondence.

## DOCUMENTS ATTACHED
- Employment contract
- Dismissal notice

## CONCLUSION
The Plaintiff requests lawyer-reviewed relief based on the facts and applicable law.`
  },
  {
    id: 2,
    name: "dismissal_firm_sample_2.md",
    content: `# DISMISSAL PROTECTION SUIT

**Case No.:** DPS-2024-205
**Court:** Labor Court Hamburg
**Date Filed:** April 12, 2024

## PLAINTIFF
**Name:** Jonas Weber
**Address:** Old Sample Address 2
**Employee ID:** EMP-205
**Position:** Engineering Manager
**Department:** Engineering
**Hire Date:** June 1, 2018

## DEFENDANT
**Company:** Example Manufacturing AG
**Address:** Old Company Address
**Legal Representative:** Board of Directors
**HR Contact:** HR Operations

## STATEMENT OF CLAIM
The Plaintiff challenges the termination and asks the court to review the validity of the dismissal.

## I. FACTUAL BACKGROUND
The termination was issued after an internal reorganization. The Plaintiff alleges alternative positions were available.

## II. LEGAL GROUNDS
The dismissal may be invalid under Section 1 KSchG. The employer should prove operational necessity and social selection. Notice under Section 622 BGB and works council consultation should be verified.

## III. RELIEF SOUGHT
The Plaintiff seeks continued employment, compensation, costs, and other appropriate relief.

## SUPPORTING EVIDENCE
Performance records, organization charts, correspondence, works council material.

## DOCUMENTS ATTACHED
- Performance records
- Organization chart

## CONCLUSION
The draft should be reviewed by counsel before filing.`
  }
];

const builtInPacks: SamplePack[] = [
  {
    id: "challenge-dismissal",
    label: "Dismissal protection suit",
    backendDocType: "dismissal_protection_suits",
    description: "Uses the challenge-provided dismissal protection examples.",
    caseData: dismissalCaseData
  },
  {
    id: "challenge-damages",
    label: "Claim for damages",
    backendDocType: "claims_for_damages",
    description: "Uses the challenge-provided damages claim examples.",
    caseData: damagesCaseData
  },
  {
    id: "firm-dismissal",
    label: "Firm dismissal pack",
    backendDocType: "custom_legal_documents",
    description: "Two editable firm-style dismissal examples for custom learning.",
    caseData: dismissalCaseData,
    sourceDocuments: starterSourceDocuments
  },
  {
    id: "commercial-damages",
    label: "Commercial damages pack",
    backendDocType: "custom_legal_documents",
    description: "Built-in commercial dispute samples for damages-style drafting.",
    caseData: damagesCaseData,
    sourceDocuments: [
      {
        id: 31,
        name: "commercial_damages_sample_1.md",
        content: `# CLAIM FOR DAMAGES

**Case No.:** CFD-2024-201
**Court:** District Court Berlin
**Date Filed:** May 3, 2024

## PLAINTIFF
**Name:** Alpha Supply GmbH
**Address:** Prior Sample Address
**Legal Representative:** Managing Director
**Registration:** HRB 12345 B

## DEFENDANT
**Name:** Beta Retail AG
**Address:** Prior Defendant Address
**Legal Representative:** Board of Directors
**Registration:** HRB 54321 B

## STATEMENT OF CLAIM
The Plaintiff seeks damages arising from breach of supply obligations.

## I. FACTUAL BACKGROUND
The parties entered into a commercial supply relationship. Defendant failed to perform according to the agreed delivery plan.

## II. LEGAL GROUNDS
The claim is based on breach of contractual obligations and recoverable damages under applicable civil law principles.

## III. DAMAGES CLAIMED
The Plaintiff claims direct damages, consequential losses, interest, and costs.

## IV. RELIEF SOUGHT
The Plaintiff requests payment, interest, costs, and further appropriate relief.

## SUPPORTING EVIDENCE
Supply agreement, invoices, correspondence, expert calculation.

## CONCLUSION
The draft requires lawyer review before filing.`
      }
    ]
  }
];

const legalDocumentCatalog = [
  {
    area: "Employment Law",
    german: "Arbeitsrecht",
    documents: ["Dismissal Protection Suit", "Warning Letter", "Response to Warning", "Employment Contract", "Amendment Agreement", "Settlement Agreement", "Termination Agreement", "Employer Notice of Termination", "Employee Resignation", "Salary Claim", "Overtime Claim", "Vacation Compensation Claim", "Employment Certificate Request", "Temporary Injunction", "Appeal"]
  },
  {
    area: "Civil Law",
    german: "Zivilrecht",
    documents: ["Claim for Damages", "Payment Claim", "Contract Breach Claim", "Debt Collection Claim", "Loan Recovery", "Warranty Claim", "Consumer Complaint", "Contract Rescission", "Contract Cancellation", "Demand Letter"]
  },
  {
    area: "Commercial / Corporate Law",
    german: "Handels- und Gesellschaftsrecht",
    documents: ["Shareholder Resolution", "Partnership Agreement", "NDA", "Service Agreement", "Software Agreement", "Licensing Agreement", "Supplier Agreement", "Distribution Agreement", "Purchase Agreement", "Commercial Litigation"]
  },
  {
    area: "Family Law",
    german: "Familienrecht",
    documents: ["Divorce Petition", "Child Custody Petition", "Child Support Claim", "Spousal Maintenance", "Property Division", "Adoption Application", "Name Change Application"]
  },
  {
    area: "Real Estate",
    german: "Immobilienrecht",
    documents: ["Lease Agreement", "Eviction Action", "Rent Increase Notice", "Security Deposit Claim", "Property Purchase Agreement", "Construction Dispute"]
  },
  {
    area: "Criminal Law",
    german: "Strafrecht",
    documents: ["Criminal Complaint", "Defense Statement", "Appeal", "Witness Statement", "Bail Application"]
  },
  {
    area: "Administrative Law",
    german: "Verwaltungsrecht",
    documents: ["Visa Appeal", "Residence Permit Appeal", "Tax Appeal", "Building Permit Appeal", "Social Benefits Appeal"]
  },
  {
    area: "Intellectual Property",
    german: "IP-Recht",
    documents: ["Trademark Registration", "Patent Application", "Copyright Infringement", "Cease and Desist Letter", "Licensing Agreement"]
  },
  {
    area: "Data Privacy / GDPR",
    german: "Datenschutzrecht",
    documents: ["GDPR Complaint", "Data Deletion Request", "Subject Access Request", "Privacy Policy", "Data Processing Agreement"]
  },
  {
    area: "Banking / Finance",
    german: "Bank- und Finanzrecht",
    documents: ["Loan Agreement", "Guarantee", "Debt Settlement", "Insurance Claim", "Investment Dispute"]
  }
];

const runnableDocumentMap: Record<string, string> = {
  "Employment Law::Dismissal Protection Suit": "challenge-dismissal",
  "Civil Law::Claim for Damages": "challenge-damages",
  "Commercial / Corporate Law::Commercial Litigation": "commercial-damages"
};

const packTopicMap: Record<string, { area: string; topic: string }> = {
  "challenge-dismissal": { area: "Employment Law", topic: "Dismissal Protection Suit" },
  "challenge-damages": { area: "Civil Law", topic: "Claim for Damages" },
  "firm-dismissal": { area: "Employment Law", topic: "Dismissal Protection Suit" },
  "commercial-damages": { area: "Commercial / Corporate Law", topic: "Commercial Litigation" }
};

const classifierPlatformMappings = [
  { label: "Kundigung", area: "Employment Law", topic: "Employer Notice of Termination" },
  { label: "Klageschrift", area: "Civil Law", topic: "Claim for Damages" },
  { label: "Schriftsatz", area: "Civil Law", topic: "Contract Breach Claim" },
  { label: "Vertrag&Vereinbarung", area: "Commercial / Corporate Law", topic: "Service Agreement" },
  { label: "Mahnung", area: "Civil Law", topic: "Demand Letter" },
  { label: "Vergleich", area: "Employment Law", topic: "Settlement Agreement" },
  { label: "Berufung", area: "Civil Law", topic: "Appeal" },
  { label: "Lizenzierung", area: "Intellectual Property", topic: "Licensing Agreement" },
  { label: "Steuererklärung", area: "Administrative Law", topic: "Tax Appeal" },
  { label: "Rechnung", area: "Civil Law", topic: "Payment Claim" }
];

const defaultUser: UserAccount = {
  name: "Hamza Khan",
  email: "hamza@example.com",
  accountType: "firm",
  role: "senior_lawyer"
};

const legalCountries = [
  { code: "DE", label: "Germany" },
  { code: "US", label: "United States" },
  { code: "GB", label: "United Kingdom" },
  { code: "FR", label: "France" },
  { code: "ES", label: "Spain" },
  { code: "IT", label: "Italy" }
];

const pagePaths: Record<Page, string> = {
  workspace: "/",
  login: "/login",
  signup: "/signup",
  library: "/library",
  classifier: "/classifier",
  history: "/history",
  profile: "/profile",
  settings: "/settings",
  admin: "/admin",
  contact: "/contact",
  about: "/about-us",
  careers: "/careers",
  privacy: "/privacy-policy",
  terms: "/terms",
  impressum: "/impressum",
  gdpr: "/gdpr"
};

function pageFromPath(pathname: string): Page {
  const normalized = decodeURIComponent(pathname).toLowerCase().replace(/\/+$/, "") || "/";
  if (normalized === "/login") {
    return "login";
  }
  if (normalized === "/signup") {
    return "signup";
  }
  if (normalized === "/library") {
    return "library";
  }
  if (normalized === "/classifier" || normalized === "/document-classifier") {
    return "classifier";
  }
  if (normalized === "/history") {
    return "history";
  }
  if (normalized === "/profile" || normalized === "/account") {
    return "profile";
  }
  if (normalized === "/settings" || normalized === "/access") {
    return "settings";
  }
  if (normalized === "/admin" || normalized === "/firm-admin") {
    return "admin";
  }
  if (normalized === "/contact" || normalized === "/contact-us") {
    return "contact";
  }
  if (normalized === "/about-us" || normalized === "/about us" || normalized === "/about") {
    return "about";
  }
  if (normalized === "/careers") {
    return "careers";
  }
  if (normalized === "/privacy-policy" || normalized === "/privacy") {
    return "privacy";
  }
  if (normalized === "/terms" || normalized === "/terms-of-service") {
    return "terms";
  }
  if (normalized === "/impressum" || normalized === "/legal-notice") {
    return "impressum";
  }
  if (normalized === "/gdpr" || normalized === "/data-processing") {
    return "gdpr";
  }
  return "workspace";
}

export default function App() {
  const [theme, setTheme] = useState<ThemeMode>("system");
  const [appLanguage, setAppLanguage] = useState<AppLanguage>("EN");
  const [mode, setMode] = useState<"built-in" | "custom">("built-in");
  const [selectedPracticeArea, setSelectedPracticeArea] = useState("Employment Law");
  const [selectedDocumentTopic, setSelectedDocumentTopic] = useState("Dismissal Protection Suit");
  const [selectedPackId, setSelectedPackId] = useState("challenge-dismissal");
  const selectedPack = builtInPacks.find((pack) => pack.id === selectedPackId) || builtInPacks[0];
  const [llmProvider, setLlmProvider] = useState("mock");
  const [model, setModel] = useState("");
  const [providerSettings, setProviderSettings] = useState<ProviderSettings>({
    provider: "mock",
    model: "",
    apiKey: "",
    baseUrl: "",
    legalCountry: "DE",
    outputLanguage: "EN"
  });
  const [legalQuestion, setLegalQuestion] = useState("Verify the legal basis and jurisdiction-specific requirements for this draft.");
  const [legalSourceUrls, setLegalSourceUrls] = useState("https://www.gesetze-im-internet.de/\nhttps://www.bundesarbeitsgericht.de/");
  const [legalVerification, setLegalVerification] = useState<LegalVerificationResult | null>(null);
  const [legalVerificationStatus, setLegalVerificationStatus] = useState("");
  const [caseData, setCaseData] = useState<Record<string, string>>(dismissalCaseData);
  const [sourceDocuments, setSourceDocuments] = useState<SourceDocument[]>(starterSourceDocuments);
  const [userPrompt, setUserPrompt] = useState("Draft in a formal court-ready style. Keep factual assertions separate from lawyer-review assumptions.");
  const [result, setResult] = useState<AgentRun | null>(null);
  const [status, setStatus] = useState("");
  const [generationLog, setGenerationLog] = useState<ExecutionLogEvent[]>([]);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState<"draft" | "trace" | "review">("draft");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [historyRecords, setHistoryRecords] = useState<FeedbackRecord[]>([]);
  const [historyStatus, setHistoryStatus] = useState("");
  const [currentPage, setCurrentPage] = useState<Page>(() => pageFromPath(window.location.pathname));
  const [authToken, setAuthToken] = useState(() => sessionStorage.getItem("legal_ai_access_token") || "");
  const [user, setUser] = useState<UserAccount | null>(() => {
    const initialPage = pageFromPath(window.location.pathname);
    const storedToken = sessionStorage.getItem("legal_ai_access_token");
    return storedToken && initialPage !== "login" && initialPage !== "signup" ? defaultUser : null;
  });
  const [authDraft, setAuthDraft] = useState<UserAccount>(defaultUser);
  const [authPassword, setAuthPassword] = useState("");
  const [authFirmName, setAuthFirmName] = useState("Example Legal Partners LLP");
  const [authStatus, setAuthStatus] = useState("");
  const [providerSaveStatus, setProviderSaveStatus] = useState("");
  const [providerConfigs, setProviderConfigs] = useState<Array<{ id: string; provider: string; model: string; base_url: string; scope: string; has_api_key: boolean }>>([]);
  const [subscriptionStatus, setSubscriptionStatus] = useState("");
  const [subscriptionInfo, setSubscriptionInfo] = useState<{ plan: string; billing_cycle: string; monthly_limit: number; used_count: number; remaining: number } | null>(null);
  const [classifierStatus, setClassifierStatus] = useState("");
  const [classifierDocuments, setClassifierDocuments] = useState<SourceDocument[]>([]);
  const [classifierResults, setClassifierResults] = useState<ClassificationResult[]>([]);
  const [classifierCoverage, setClassifierCoverage] = useState<ClassifierCoverage | null>(null);
  const [learningStatus, setLearningStatus] = useState("");
  const [learnedDrafts, setLearnedDrafts] = useState<SourceDocument[]>([]);
  const [adminStatus, setAdminStatus] = useState("");
  const [adminOverview, setAdminOverview] = useState<Record<string, unknown> | null>(null);
  const progressTemplate: ExecutionLogEvent[] = [
    { agent: "RequestGateway", phase: "intake", status: "queued", message: "Waiting to receive and validate the request input." },
    { agent: "BillingAgent", phase: "plan", status: "queued", message: "Checking role, account scope, and monthly draft quota." },
    { agent: "ProviderRouter", phase: "plan", status: "queued", message: "Selecting model provider and preparing the LLM client." },
    { agent: "DocumentParserAgent", phase: "observe", status: "queued", message: "Reading source examples and normalizing document content." },
    { agent: "PlanningAgent", phase: "plan", status: "queued", message: "Planning which agents and tools should handle this draft." },
    { agent: "LLMPatternAgent", phase: "analyze", status: "queued", message: "Recognizing legal patterns, variables, repeated clauses, and required sections." },
    { agent: "RetrievalAgent", phase: "observe", status: "queued", message: "Retrieving RAG grounding chunks from source examples." },
    { agent: "GroundedDraftingAgent", phase: "act", status: "queued", message: "Drafting from facts, template, retrieved chunks, and user prompt." },
    { agent: "CritiqueAgent", phase: "analyze", status: "queued", message: "Checking QA findings, missing facts, and legal-review risks." },
    { agent: "RevisionAgent", phase: "act", status: "queued", message: "Reforming the draft when critique recommends revision." },
    { agent: "HumanReviewAgent", phase: "observe", status: "queued", message: "Preparing review packet, trace artifacts, and feedback record hooks." },
    { agent: "ResponseAssembler", phase: "act", status: "queued", message: "Preparing final draft response for the workspace." }
  ];

  const activeDocType = mode === "built-in" ? selectedPack.backendDocType : "custom_legal_documents";
  const copy = uiCopy[appLanguage];
  const activeFields = fieldsFor(activeDocType, selectedPack.id);
  const missingRequired = activeFields.filter((field) => field.required && !String(caseData[field.key] || "").trim());
  const sourceDocumentsToSend = mode === "custom" ? sourceDocuments : selectedPack.sourceDocuments;
  const accountScope = user?.accountType || "guest";
  const firmId = user?.accountType === "firm" ? user.firm_id || "11111111-1111-4111-8111-111111111111" : "";
  const userEmail = user?.email || "guest";

  function apiHeaders(extra: Record<string, string> = {}) {
    return authToken ? { ...extra, Authorization: `Bearer ${authToken}` } : extra;
  }

  function applyAuthenticatedUser(nextUser: UserAccount, token: string) {
    setUser(nextUser);
    setAuthDraft(nextUser);
    setAuthToken(token);
    sessionStorage.setItem("legal_ai_access_token", token);
  }

  function startGenerationProgress() {
    setGenerationLog(progressTemplate.map((event, index) => ({ ...event, status: index === 0 ? "running" : "queued" })));
    let cancelled = false;
    const done = (async () => {
      for (let activeIndex = 0; activeIndex < progressTemplate.length; activeIndex += 1) {
        if (cancelled) {
          return;
        }
        setGenerationLog(
          progressTemplate.map((event, index) => ({
            ...event,
            status: index < activeIndex ? "completed" : index === activeIndex ? "running" : "queued"
          }))
        );
        await wait(1150);
      }
      if (!cancelled) {
        setGenerationLog(progressTemplate.map((event) => ({ ...event, status: "completed" })));
      }
    })();
    return {
      done,
      cancel: () => {
        cancelled = true;
      }
    };
  }

  function wait(ms: number) {
    return new Promise<void>((resolve) => window.setTimeout(resolve, ms));
  }

  function failRunningProgress(message: string) {
    setGenerationLog((current) =>
      current.map((event) => (event.status === "running" ? { ...event, status: "failed", message } : event))
    );
  }

  const completionPercent = useMemo(() => {
    const required = activeFields.filter((field) => field.required);
    if (!required.length) {
      return 100;
    }
    const filled = required.filter((field) => String(caseData[field.key] || "").trim()).length;
    return Math.round((filled / required.length) * 100);
  }, [activeFields, caseData]);

  useEffect(() => {
    const syncFromBrowserPath = () => setCurrentPage(pageFromPath(window.location.pathname));
    window.addEventListener("popstate", syncFromBrowserPath);
    return () => window.removeEventListener("popstate", syncFromBrowserPath);
  }, []);

  useEffect(() => {
    if (!authToken) {
      return;
    }
    fetch("/api/auth/me", { headers: apiHeaders() })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(body.detail || "Session expired.");
        }
        setUser(body.user);
        setAuthDraft(body.user);
      })
      .catch(() => {
        setAuthToken("");
        setUser(null);
        sessionStorage.removeItem("legal_ai_access_token");
      });
  }, [authToken]);

  useEffect(() => {
    if (currentPage === "history") {
      void loadHistory();
    }
    if (currentPage === "settings") {
      void loadSubscription();
      void loadProviderConfigs();
    }
    if (currentPage === "admin") {
      void loadFirmAdminOverview();
    }
  }, [currentPage]);

  useEffect(() => {
    const titles: Record<Page, string> = {
      workspace: "Legal AI Pattern Drafting Studio",
      login: "Login | Legal AI Pattern Drafting Studio",
      signup: "Signup | Legal AI Pattern Drafting Studio",
      library: "Sample Library | Legal AI Pattern Drafting Studio",
      classifier: "Document Classifier | Legal AI Pattern Drafting Studio",
      history: "History | Legal AI Pattern Drafting Studio",
      profile: "Profile | Legal AI Pattern Drafting Studio",
      settings: "Settings | Legal AI Pattern Drafting Studio",
      admin: "Firm Admin | Legal AI Pattern Drafting Studio",
      contact: "Contact | Legal AI Pattern Drafting Studio",
      about: "About Us | Legal AI Pattern Drafting Studio",
      careers: "Careers | Legal AI Pattern Drafting Studio",
      privacy: "Privacy Policy | Legal AI Pattern Drafting Studio",
      terms: "Terms | Legal AI Pattern Drafting Studio",
      impressum: "Impressum | Legal AI Pattern Drafting Studio",
      gdpr: "GDPR | Legal AI Pattern Drafting Studio"
    };
    document.title = titles[currentPage];
  }, [currentPage]);

  function navigateToPage(page: Page) {
    setCurrentPage(page);
    const nextPath = pagePaths[page];
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function selectPracticeArea(area: string) {
    const group = legalDocumentCatalog.find((item) => item.area === area) || legalDocumentCatalog[0];
    const nextTopic = group.documents[0];
    setSelectedPracticeArea(group.area);
    setSelectedDocumentTopic(nextTopic);
    applyTopicSelection(group.area, nextTopic);
  }

  function selectDocumentTopic(topic: string) {
    setSelectedDocumentTopic(topic);
    applyTopicSelection(selectedPracticeArea, topic);
  }

  function openCatalogTopic(area: string, topic: string) {
    setSelectedPracticeArea(area);
    setSelectedDocumentTopic(topic);
    applyTopicSelection(area, topic);
    navigateToPage("workspace");
  }

  function applyTopicSelection(area: string, topic: string) {
    const packId = runnableDocumentMap[`${area}::${topic}`];
    if (packId) {
      applySamplePack(packId);
      setMode("built-in");
    } else {
      setMode("custom");
      setCaseData({
        ...Object.fromEntries(customFields.map((field) => [field.key, ""])),
        case_no: `${topic.toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 12) || "MATTER"}-2026-001`,
        date_filed: new Date().toISOString().slice(0, 10),
        matter_summary: `${topic} matter in ${area}. Add client facts, opposing party details, requested relief, and supporting evidence before generation.`
      });
      setSourceDocuments([
        {
          id: Date.now(),
          name: `${topic.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_sample.md`,
          content: `# ${topic.toUpperCase()}\n\n## PARTIES\n\n## FACTUAL BACKGROUND\n\n## LEGAL BASIS\n\n## REQUESTED RELIEF\n\n## SUPPORTING EVIDENCE\n\n## CONCLUSION\n`
        }
      ]);
      setResult(null);
    }
  }

  function applySamplePack(packId: string) {
    const pack = builtInPacks.find((item) => item.id === packId) || builtInPacks[0];
    const topic = packTopicMap[pack.id];
    setSelectedPackId(pack.id);
    if (topic) {
      setSelectedPracticeArea(topic.area);
      setSelectedDocumentTopic(topic.topic);
    }
    setCaseData(pack.caseData);
    if (pack.sourceDocuments) {
      setSourceDocuments(pack.sourceDocuments);
    }
    setResult(null);
  }

  function updateCaseField(key: string, value: string) {
    setCaseData((current) => ({ ...current, [key]: value }));
  }

  async function loadCaseFactsFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const text = await file.text();
    try {
      const parsed = JSON.parse(text);
      setCaseData((current) => ({ ...current, ...stringRecord(parsed) }));
      setError("");
    } catch {
      setCaseData((current) => ({ ...current, ...parseLooseKeyValues(text) }));
      setError("");
    }
  }

  async function generateDraft() {
    if (missingRequired.length) {
      setError(`Missing required fields: ${missingRequired.map((field) => field.label).join(", ")}`);
      return;
    }

    setError("");
    setResult(null);
    setStatus("Request submitted. Agents are starting the drafting workflow...");
    const progress = startGenerationProgress();

    const payload = {
      doc_type: activeDocType,
      llm_provider: llmProvider,
      model: model || undefined,
      api_key: providerSettings.apiKey || undefined,
      base_url: providerSettings.baseUrl || undefined,
      legal_country: providerSettings.legalCountry,
      output_language: providerSettings.outputLanguage,
      case_data: {
        ...caseData,
        user_prompt: userPrompt,
        requested_by: userEmail,
        account_scope: accountScope,
        firm_id: firmId,
        legal_country: providerSettings.legalCountry,
        output_language: providerSettings.outputLanguage,
        reviewer_visibility: user?.role === "junior_lawyer" ? "assigned_senior_only" : "firm_senior_review"
      },
      source_documents: sourceDocumentsToSend?.map(({ name, content }) => ({ name, content })),
      account_scope: accountScope,
      firm_id: firmId,
      user_email: userEmail
    };

    try {
      try {
        const health = await fetch("/health");
        if (!health.ok) {
          throw new Error("Backend health check failed.");
        }
      } catch {
        throw new Error("Backend API is not reachable. Start the FastAPI backend on port 8001, then generate again.");
      }

      const response = await fetch("/generate", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Draft generation failed.");
      }

      const body = await response.json();
      setStatus("Finalizing draft...");
      await progress.done;
      setResult(body);
      setGenerationLog(progressTemplate.map((event) => ({ ...event, status: "completed" })));
      setActiveView("draft");
      setFeedbackComment("");
      setFeedbackStatus("");
      setStatus("");
      window.setTimeout(() => setGenerationLog([]), 1800);
    } catch (caught) {
      progress.cancel();
      setStatus("");
      const message = caught instanceof Error ? caught.message : "Draft generation failed. Check backend logs and required inputs.";
      failRunningProgress(message);
      setError(message);
    }
  }

  function addSourceDocument() {
    setSourceDocuments((current) => [
      ...current,
      { id: Date.now(), name: `firm_sample_${current.length + 1}.md`, content: "# LEGAL DOCUMENT\n\n## PLAINTIFF\n\n## DEFENDANT\n\n## STATEMENT OF CLAIM\n" }
    ]);
  }

  function updateSourceDocument(id: number, patch: Partial<SourceDocument>) {
    setSourceDocuments((current) => current.map((doc) => (doc.id === id ? { ...doc, ...patch } : doc)));
  }

  async function loadSourceFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    const loaded = await Promise.all(
      files.map(async (file, index) => ({
        id: Date.now() + index,
        name: file.name,
        content: await file.text()
      }))
    );
    if (loaded.length) {
      setMode("custom");
      setSourceDocuments(loaded);
      await classifyUploadedDocument(loaded[0]);
    }
  }

  async function classifyUploadedDocument(document: SourceDocument) {
    setClassifierStatus("Classifying uploaded document before routing...");
    try {
      const response = await fetch("/api/classify-document", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ filename: document.name, content: document.content })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Document classification failed.");
      }
      if (body.practice_area && body.topic) {
        setSelectedPracticeArea(body.practice_area);
        setSelectedDocumentTopic(body.topic);
      }
      if (body.pack_id) {
        setSelectedPackId(body.pack_id);
      }
      setClassifierStatus(`Classifier: ${body.topic || body.document_type} (${Math.round(Number(body.confidence || 0) * 100)}% confidence).`);
    } catch (caught) {
      setClassifierStatus(caught instanceof Error ? caught.message : "Document classification failed.");
    }
  }

  async function loadClassifierFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    const loaded = await Promise.all(
      files.map(async (file, index) => ({
        id: Date.now() + index,
        name: file.name,
        content: await file.text()
      }))
    );
    if (loaded.length) {
      setClassifierDocuments(loaded);
      setClassifierResults([]);
      setClassifierCoverage(null);
      setClassifierStatus(`${loaded.length} document${loaded.length === 1 ? "" : "s"} ready for classification.`);
    }
  }

  function addClassifierTextSample() {
    setClassifierDocuments((current) => [
      ...current,
      {
        id: Date.now(),
        name: `pasted_document_${current.length + 1}.txt`,
        content: "Paste or type a legal document here before classification."
      }
    ]);
  }

  function updateClassifierDocument(id: number, patch: Partial<SourceDocument>) {
    setClassifierDocuments((current) => current.map((doc) => (doc.id === id ? { ...doc, ...patch } : doc)));
  }

  async function classifyDocuments() {
    const ready = classifierDocuments.filter((document) => document.content.trim());
    if (!ready.length) {
      setClassifierStatus("Upload or paste at least one document first.");
      return;
    }
    setClassifierStatus("Classifying documents and preparing routing suggestions...");
    try {
      const response = await fetch("/api/classify-documents", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          documents: ready.map((document) => ({ filename: document.name, content: document.content }))
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Document classification failed.");
      }
      setClassifierResults(body.results || []);
      setClassifierCoverage(body.coverage || null);
      setClassifierStatus(`Classified ${body.results?.length || 0} document${body.results?.length === 1 ? "" : "s"}.`);
    } catch (caught) {
      setClassifierStatus(caught instanceof Error ? caught.message : "Document classification failed.");
    }
  }

  function routeClassificationToWorkspace(resultItem: ClassificationResult) {
    const area = resultItem.practice_area || "Civil Law";
    const topic = resultItem.topic || resultItem.document_type || "Custom legal document";
    openCatalogTopic(area, normalizeClassifierTopic(area, topic));
  }

  function addClassificationAsWorkspaceSource(resultItem: ClassificationResult) {
    const source = classifierDocuments[resultItem.index ?? 0];
    if (!source) {
      setClassifierStatus("Could not find the classified source document.");
      return;
    }
    setMode("custom");
    setSourceDocuments((current) => [
      ...current,
      {
        ...source,
        id: Date.now(),
        name: `${source.name.replace(/\.[^.]+$/, "")}_classified_source.md`
      }
    ]);
    routeClassificationToWorkspace(resultItem);
    setClassifierStatus("Added classified document as a Workspace source example.");
  }

  async function saveLearnedDraft(title: string, content: string, learnMode: "add" | "update" = "add") {
    if (!authToken) {
      setLearningStatus("Log in before saving drafts for learning.");
      return;
    }
    if (!content.trim()) {
      setLearningStatus("No draft content available to learn from.");
      return;
    }
    setLearningStatus(learnMode === "update" ? "Updating learned draft patterns..." : "Learning from draft and adding it to source examples...");
    try {
      const response = await fetch("/api/learned-drafts", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          title,
          document_type: activeDocType,
          content,
          learn_mode: learnMode,
          legal_country: providerSettings.legalCountry
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Could not save learned draft.");
      }
      setLearningStatus(`${body.message} ${body.chunks_saved} chunks saved.`);
      await loadLearnedDrafts();
    } catch (caught) {
      setLearningStatus(caught instanceof Error ? caught.message : "Could not save learned draft.");
    }
  }

  async function loadLearnedDrafts() {
    if (!authToken) {
      setLearningStatus("Log in to load learned drafts.");
      return;
    }
    setLearningStatus("Loading learned drafts...");
    try {
      const response = await fetch("/api/learned-drafts", { headers: apiHeaders() });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Could not load learned drafts.");
      }
      const drafts = (body.drafts || []).map((draft: { name?: string; content?: string }, index: number) => ({
        id: Date.now() + index,
        name: draft.name || `learned_draft_${index + 1}.md`,
        content: draft.content || ""
      }));
      setLearnedDrafts(drafts);
      setLearningStatus(`${drafts.length} learned draft chunks loaded.`);
    } catch (caught) {
      setLearningStatus(caught instanceof Error ? caught.message : "Could not load learned drafts.");
    }
  }

  async function learnUploadedDrafts(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
      return;
    }
    for (const file of files) {
      await saveLearnedDraft(file.name, await file.text(), "add");
    }
  }

  function useLearnedDraftsAsSources() {
    if (!learnedDrafts.length) {
      setLearningStatus("Load learned drafts first.");
      return;
    }
    setMode("custom");
    setSourceDocuments(learnedDrafts);
    setLearningStatus("Loaded learned drafts into source examples for the next generation.");
  }

  async function exportDraft(format: "md" | "docx" | "pdf") {
    if (!result?.draft_markdown) {
      setFeedbackStatus("Generate a draft before exporting.");
      return;
    }
    try {
      const response = await fetch("/api/export/draft", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          filename: `${result.document_type}_${result.run_id}`,
          draft_markdown: result.draft_markdown,
          format
        })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Export failed.");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${result.document_type}_${result.run_id}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (caught) {
      setFeedbackStatus(caught instanceof Error ? caught.message : "Export failed.");
    }
  }

  async function submitAuth() {
    setAuthStatus("Connecting to secure backend...");
    try {
      const signup = currentPage === "signup";
      const response = await fetch(signup ? "/api/auth/register" : "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          signup
            ? {
                full_name: authDraft.name,
                email: authDraft.email,
                password: authPassword,
                account_type: authDraft.accountType,
                role: authDraft.role,
                firm_name: authFirmName
              }
            : {
                email: authDraft.email,
                password: authPassword
              }
        )
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Authentication failed.");
      }
      applyAuthenticatedUser(body.user, body.access_token);
      setAuthPassword("");
      setAuthStatus("");
      navigateToPage("workspace");
    } catch (caught) {
      setAuthStatus(caught instanceof Error ? caught.message : "Authentication failed.");
    }
  }

  function updateProviderSettings(patch: Partial<ProviderSettings>) {
    setProviderSettings((current) => {
      const next = { ...current, ...patch };
      setLlmProvider(next.provider);
      setModel(next.model);
      return next;
    });
  }

  async function verifyLegalSources() {
    setLegalVerificationStatus("Checking official-source policy...");
    setLegalVerification(null);
    try {
      const response = await fetch("/api/legal-verification", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          country: providerSettings.legalCountry,
          legal_question: legalQuestion,
          source_urls: legalSourceUrls.split(/\r?\n/).map((url) => url.trim()).filter(Boolean)
        })
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Legal verification failed.");
      }
      setLegalVerification(body);
      setLegalVerificationStatus(body.verification_status);
    } catch (caught) {
      setLegalVerificationStatus(caught instanceof Error ? caught.message : "Legal verification failed.");
    }
  }

  async function saveProviderConfig() {
    if (!authToken) {
      setProviderSaveStatus("Log in before saving provider settings.");
      return;
    }
    setProviderSaveStatus("Saving encrypted provider configuration...");
    try {
      const response = await fetch("/api/provider-config", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          provider: providerSettings.provider,
          model: providerSettings.model,
          base_url: providerSettings.baseUrl,
          api_key: providerSettings.apiKey,
          scope: user?.accountType === "firm" ? "firm" : "user",
          legal_country: providerSettings.legalCountry
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Provider settings could not be saved.");
      }
      setProviderSaveStatus("Provider settings saved. API key is never returned to the browser.");
      await loadProviderConfigs();
    } catch (caught) {
      setProviderSaveStatus(caught instanceof Error ? caught.message : "Provider settings could not be saved.");
    }
  }

  async function loadProviderConfigs() {
    if (!authToken) {
      setProviderConfigs([]);
      return;
    }
    try {
      const response = await fetch("/api/provider-config", { headers: apiHeaders() });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Could not load provider settings.");
      }
      setProviderConfigs(body.configs || []);
    } catch {
      setProviderConfigs([]);
    }
  }

  async function loadSubscription() {
    if (!authToken) {
      setSubscriptionInfo(null);
      setSubscriptionStatus("Log in to see subscription and usage limits.");
      return;
    }
    setSubscriptionStatus("Loading subscription...");
    try {
      const response = await fetch("/api/subscription", { headers: apiHeaders() });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Could not load subscription.");
      }
      setSubscriptionInfo({
        plan: body.subscription.plan_code,
        billing_cycle: body.subscription.billing_cycle,
        monthly_limit: body.subscription.draft_limit,
        used_count: body.usage.draft_generations,
        remaining: Math.max(0, Number(body.subscription.draft_limit || 0) - Number(body.usage.draft_generations || 0))
      });
      setSubscriptionStatus("");
    } catch (caught) {
      setSubscriptionStatus(caught instanceof Error ? caught.message : "Could not load subscription.");
    }
  }

  async function loadFirmAdminOverview() {
    if (!authToken) {
      setAdminOverview(null);
      setAdminStatus("Log in with a firm account to use firm admin.");
      return;
    }
    setAdminStatus("Loading firm admin workspace...");
    try {
      const response = await fetch("/api/firm-admin/overview", { headers: apiHeaders() });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Could not load firm admin workspace.");
      }
      setAdminOverview(body);
      setAdminStatus("");
    } catch (caught) {
      setAdminOverview(null);
      setAdminStatus(caught instanceof Error ? caught.message : "Could not load firm admin workspace.");
    }
  }

  async function inviteFirmUser(email: string, role: UserAccount["role"]) {
    setAdminStatus("Sending firm invitation...");
    try {
      const response = await fetch("/api/firm-admin/invite", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ email, role, message: "You have been invited to Legal AI Pattern Studio." })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Invitation failed.");
      }
      setAdminStatus(`Invitation queued for ${email}.`);
    } catch (caught) {
      setAdminStatus(caught instanceof Error ? caught.message : "Invitation failed.");
    }
  }

  async function assignMatter(matter_title: string, assignee_email: string, document_type: string) {
    setAdminStatus("Assigning matter...");
    try {
      const response = await fetch("/api/firm-admin/assign", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ matter_title, assignee_email, document_type, instructions: "Prepare draft for senior review." })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Assignment failed.");
      }
      setAdminStatus(`Matter assigned to ${assignee_email}.`);
    } catch (caught) {
      setAdminStatus(caught instanceof Error ? caught.message : "Assignment failed.");
    }
  }

  async function loadHistory() {
    setHistoryStatus("Loading saved review history...");
    try {
      const params = new URLSearchParams({ account_scope: accountScope, firm_id: firmId, user_email: userEmail });
      const response = await fetch(`/api/history?${params.toString()}`, { headers: apiHeaders() });
      if (!response.ok) {
        throw new Error("Could not load history.");
      }
      const body = await response.json();
      setHistoryRecords([...(body.positive || []), ...(body.negative || [])]);
      setHistoryStatus("");
    } catch (caught) {
      setHistoryStatus(caught instanceof Error ? caught.message : "Could not load history.");
    }
  }

  async function saveFeedback(sentiment: "positive" | "negative") {
    if (!result) {
      return;
    }
    setFeedbackStatus("Saving feedback...");
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          run_id: result.run_id,
          sentiment,
          comment: feedbackComment,
          document_type: result.document_type,
          draft_markdown: result.draft_markdown || "",
          case_data: caseData,
          qa_score: result.final_qa_score,
          reviewer: userEmail,
          account_scope: accountScope,
          firm_id: firmId,
          user_email: userEmail
        })
      });
      if (!response.ok) {
        throw new Error("Feedback could not be saved.");
      }
      const body = await response.json();
      setHistoryRecords((current) => [body.record, ...current]);
      setFeedbackStatus(sentiment === "positive" ? "Saved to Positive History." : "Saved to Negative History.");
      setFeedbackComment("");
    } catch (caught) {
      setFeedbackStatus(caught instanceof Error ? caught.message : "Feedback could not be saved.");
    }
  }

  return (
    <main className="app-shell" data-theme={theme}>
      <NeuralBackdrop />
      <AppNavbar
        currentPage={currentPage}
        user={user}
        theme={theme}
        setTheme={setTheme}
        appLanguage={appLanguage}
        setAppLanguage={setAppLanguage}
        llmProvider={llmProvider}
        copy={copy}
        onNavigate={navigateToPage}
        onSignOut={() => {
          setAuthToken("");
          setUser(null);
          sessionStorage.removeItem("legal_ai_access_token");
          navigateToPage("login");
        }}
      />
      <div className="page-content">
        {currentPage === "login" || currentPage === "signup" ? (
          <AuthPage
            mode={currentPage}
            authDraft={authDraft}
            setAuthDraft={setAuthDraft}
            authPassword={authPassword}
            setAuthPassword={setAuthPassword}
            authFirmName={authFirmName}
            setAuthFirmName={setAuthFirmName}
            authStatus={authStatus}
            submitAuth={submitAuth}
            switchMode={navigateToPage}
          />
        ) : currentPage === "library" ? (
          <DocumentLibraryPage
            onUsePack={(packId) => {
              applySamplePack(packId);
              setMode("built-in");
              navigateToPage("workspace");
            }}
            onUseTopic={openCatalogTopic}
          />
        ) : currentPage === "classifier" ? (
          <DocumentClassifierPage
            documents={classifierDocuments}
            results={classifierResults}
            coverage={classifierCoverage}
            status={classifierStatus}
            onLoadFiles={loadClassifierFiles}
            onAddTextSample={addClassifierTextSample}
            onUpdateDocument={updateClassifierDocument}
            onClassify={classifyDocuments}
            onRouteToWorkspace={routeClassificationToWorkspace}
            onAddAsSource={addClassificationAsWorkspaceSource}
          />
        ) : currentPage === "history" ? (
          <HistoryPage records={historyRecords} status={historyStatus} onRefresh={loadHistory} />
        ) : currentPage === "profile" ? (
          <ProfilePage user={user} setUser={setUser} authToken={authToken} apiHeaders={apiHeaders} />
        ) : currentPage === "settings" ? (
          <SettingsPage
            user={user}
            theme={theme}
            setTheme={setTheme}
            appLanguage={appLanguage}
            setAppLanguage={setAppLanguage}
            providerSettings={providerSettings}
            updateProviderSettings={updateProviderSettings}
            legalQuestion={legalQuestion}
            setLegalQuestion={setLegalQuestion}
            legalSourceUrls={legalSourceUrls}
            setLegalSourceUrls={setLegalSourceUrls}
            legalVerification={legalVerification}
            legalVerificationStatus={legalVerificationStatus}
            verifyLegalSources={verifyLegalSources}
            saveProviderConfig={saveProviderConfig}
            providerSaveStatus={providerSaveStatus}
            providerConfigs={providerConfigs}
            subscriptionInfo={subscriptionInfo}
            subscriptionStatus={subscriptionStatus}
            onRefreshSubscription={loadSubscription}
          />
        ) : currentPage === "admin" ? (
          <FirmAdminPage
            user={user}
            overview={adminOverview}
            status={adminStatus}
            onRefresh={loadFirmAdminOverview}
            onInvite={inviteFirmUser}
            onAssign={assignMatter}
          />
        ) : currentPage === "contact" ? (
          <ContactPage user={user} authToken={authToken} apiHeaders={apiHeaders} />
        ) : currentPage === "about" ? (
          <AboutPage />
        ) : currentPage === "careers" ? (
          <CareersPage />
        ) : currentPage === "privacy" ? (
          <PrivacyPolicyPage />
        ) : currentPage === "terms" ? (
          <LegalInfoPage kind="terms" />
        ) : currentPage === "impressum" ? (
          <LegalInfoPage kind="impressum" />
        ) : currentPage === "gdpr" ? (
          <LegalInfoPage kind="gdpr" />
        ) : (
          <>
      <section className="topbar">
        <div>
          <p className="eyebrow">{copy.workspaceEyebrow}</p>
          <h1>{copy.workspaceTitle}</h1>
          <p className="subtitle">{copy.workspaceSubtitle}</p>
        </div>
      </section>

      <section className="workspace">
        <aside className="control-panel">
          <div className="panel-section">
            <div className="section-title">
              <h2>{copy.sourceLearning}</h2>
              <span>{mode === "built-in" ? copy.runnableSample : copy.customRoadmap}</span>
            </div>
            <div className="two-col">
              <label>
                {copy.practiceArea}
                <select value={selectedPracticeArea} onChange={(event) => selectPracticeArea(event.target.value)}>
                  {legalDocumentCatalog.map((group) => (
                    <option value={group.area} key={group.area}>{group.area}</option>
                  ))}
                </select>
              </label>
              <label>
                {copy.documentType}
                <select value={selectedDocumentTopic} onChange={(event) => selectDocumentTopic(event.target.value)}>
                  {(legalDocumentCatalog.find((group) => group.area === selectedPracticeArea)?.documents || []).map((document) => (
                    <option value={document} key={document}>{document}</option>
                  ))}
                </select>
              </label>
            </div>
            <p className="field-note">
              {copy.taxonomyNote}
            </p>
            <div className="segmented">
              <button className={mode === "built-in" ? "active" : ""} onClick={() => setMode("built-in")}>{copy.builtInSamples}</button>
              <button className={mode === "custom" ? "active" : ""} onClick={() => setMode("custom")}>{copy.mySamples}</button>
            </div>

            {mode === "built-in" ? (
              <>
                <label>
                  {copy.builtInPack}
                  <select value={selectedPackId} onChange={(event) => applySamplePack(event.target.value)}>
                    {builtInPacks.map((pack) => (
                      <option value={pack.id} key={pack.id}>{pack.label}</option>
                    ))}
                  </select>
                </label>
                <p className="field-note">{selectedPack.description}</p>
              </>
            ) : (
              <div className="source-stack">
                <label className="file-drop">
                  <span>Upload Markdown or text samples</span>
                  <input multiple type="file" accept=".md,.txt" onChange={loadSourceFiles} />
                </label>
                <div className="learning-panel">
                  <div>
                    <strong>Learn from firm drafts</strong>
                    <p className="field-note">Upload prior drafts so the agents can classify, chunk, retrieve, and reuse firm-specific drafting patterns.</p>
                  </div>
                  <label className="file-drop slim">
                    <span>Add learned drafts</span>
                    <input multiple type="file" accept=".md,.txt" onChange={learnUploadedDrafts} />
                  </label>
                  <div className="button-row">
                    <button className="secondary" onClick={loadLearnedDrafts}>Load learned drafts</button>
                    <button className="secondary" onClick={useLearnedDraftsAsSources}>Use learned drafts as sources</button>
                  </div>
                </div>
                {classifierStatus && <p className="status">{classifierStatus}</p>}
                {learningStatus && <p className="status">{learningStatus}</p>}
                {sourceDocuments.map((doc) => (
                  <article className="source-card" key={doc.id}>
                    <input value={doc.name} onChange={(event) => updateSourceDocument(doc.id, { name: event.target.value })} />
                    <textarea value={doc.content} onChange={(event) => updateSourceDocument(doc.id, { content: event.target.value })} rows={7} />
                  </article>
                ))}
                <button className="secondary" onClick={addSourceDocument}>Add sample</button>
              </div>
            )}
          </div>

          <div className="panel-section">
            <div className="section-title">
              <h2>{copy.newCaseFacts}</h2>
              <span>{completionPercent}% {copy.requiredComplete}</span>
            </div>
            <p className="field-note">
              {copy.factsNote}
            </p>
            <label className="file-drop slim">
              <span>{copy.uploadIntake}</span>
              <input type="file" accept=".json,.txt,.md" onChange={loadCaseFactsFile} />
            </label>
            <div className="facts-grid">
              {activeFields.map((field) => (
                <FieldInput key={field.key} field={field} value={caseData[field.key] || ""} onChange={updateCaseField} />
              ))}
            </div>
          </div>

          <div className="panel-section">
            <h2>Drafting Note</h2>
            <p className="field-note">
              Saved with the case facts and passed into the drafting request. Production would store this as a versioned
              prompt instruction with reviewer approval.
            </p>
            <textarea className="prompt-box" value={userPrompt} onChange={(event) => setUserPrompt(event.target.value)} rows={5} />
          </div>

          <div className="panel-section">
            <h2>Generation</h2>
            <div className="two-col">
              <label>
                LLM
                <select value={llmProvider} onChange={(event) => setLlmProvider(event.target.value)}>
                  <option value="mock">Mock LLM</option>
                  <option value="ollama">Ollama</option>
                  <option value="openai-compatible">OpenAI-compatible</option>
                </select>
              </label>
              <label>
                Model
                <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="llama3.1:8b" />
              </label>
              <label>
                Draft language
                <select value={providerSettings.outputLanguage} onChange={(event) => updateProviderSettings({ outputLanguage: event.target.value as AppLanguage })}>
                  {appLanguages.map((language) => (
                    <option value={language.code} key={language.code}>{language.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <button className="primary" disabled={Boolean(status)} onClick={generateDraft}>
              {status ? "Generating..." : "Generate draft"}
            </button>
            {status && <p className="status">{status}</p>}
            {error && <p className="error">{error}</p>}
            {generationLog.length > 0 && (
              <ExecutionLogPanel
                title={status ? "Live Agent Progress" : "Last Run Log"}
                events={generationLog}
                compact
              />
            )}
          </div>
        </aside>

        <section className="result-panel">
          <AccessStrip user={user} onOpenAccess={() => navigateToPage("settings")} />
          {!result && (
            <div className="empty-state">
              <p className="eyebrow">{copy.readyForDrafting}</p>
              <h2>{copy.emptyTitle}</h2>
              <p>{copy.emptyText}</p>
            </div>
          )}

          {result && (
            <>
              <div className="score-grid">
                <Metric label="Initial QA" value={`${Math.round(result.initial_qa_score * 100)}%`} />
                <Metric label="Final QA" value={`${Math.round(result.final_qa_score * 100)}%`} strong />
                <Metric label="Retrieval" value={`${Math.round(result.retrieval_coverage * 100)}%`} />
                <Metric label="Run" value={result.run_id.slice(-7)} />
              </div>

              <div className="tabs">
                <button className={activeView === "draft" ? "active" : ""} onClick={() => setActiveView("draft")}>Draft</button>
                <button className={activeView === "trace" ? "active" : ""} onClick={() => setActiveView("trace")}>Agent Trace</button>
                <button className={activeView === "review" ? "active" : ""} onClick={() => setActiveView("review")}>Review</button>
              </div>

              {activeView === "draft" && (
                <article className="draft-view">
                  <header>
                    <span>{result.document_type.replaceAll("_", " ")}</span>
                    <strong>Final QA {Math.round(result.final_qa_score * 100)}%</strong>
                  </header>
                  <div className="export-actions">
                    <button className="secondary small" onClick={() => exportDraft("md")}>Download Markdown</button>
                    <button className="secondary small" onClick={() => exportDraft("docx")}>Download DOCX</button>
                    <button className="secondary small" onClick={() => exportDraft("pdf")}>Download PDF</button>
                  </div>
                  <pre>{result.draft_markdown || "Draft artifact was not returned by the backend."}</pre>
                </article>
              )}

              {activeView === "trace" && (
                <>
                  <ExecutionLogPanel title="Execution Log" events={result.execution_log || generationLog} />
                  <div className="timeline">
                    {result.steps.map((step, index) => (
                      <article className="timeline-item" key={`${step.name}-${index}`}>
                        <div className="step-index">{index + 1}</div>
                        <div>
                          <h3>{step.name}</h3>
                          <p>{step.purpose}</p>
                          <span>{step.output_summary}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                </>
              )}

              {activeView === "review" && (
                <article className="review-card">
                  <h2>Lawyer Review Packet</h2>
                  <p>Status: {result.human_review?.status || "pending_lawyer_review"}</p>
                  <p>Trace: {result.trace_dir}</p>
                  {result.legal_validation && (
                    <div className="verification-result">
                      <strong>Automatic legal citation validation: {result.legal_validation.status}</strong>
                      <p>Country: {result.legal_validation.country}</p>
                      <p>Detected citations: {result.legal_validation.detected_citations.join(", ") || "None detected"}</p>
                      <small>{result.legal_validation.instruction}</small>
                    </div>
                  )}
                  <ul>
                    {(result.human_review?.review_reasons || [
                      "Generated legal document requires qualified lawyer review.",
                      "Grounding and citations should be checked before filing."
                    ]).map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                  <div className="feedback-box">
                    <h3>Reviewer Feedback</h3>
                    <p>Save the generated output with your review note. Positive feedback improves approved-history examples; negative feedback is separated for failure analysis.</p>
                    <textarea
                      value={feedbackComment}
                      onChange={(event) => setFeedbackComment(event.target.value)}
                      placeholder="Add reviewer comments, missing facts, legal concerns, or approval notes..."
                      rows={4}
                    />
                    <div className="feedback-actions">
                      <button className="primary" onClick={() => saveFeedback("positive")}>Save positive feedback</button>
                      <button className="danger-button" onClick={() => saveFeedback("negative")}>Save negative feedback</button>
                    </div>
                    <div className="feedback-actions">
                      <button className="secondary" onClick={() => saveLearnedDraft(`${result.document_type}_${result.run_id}`, result.draft_markdown || "", "add")}>Learn from this draft</button>
                      <button className="secondary" onClick={() => saveLearnedDraft(`${result.document_type}_${result.run_id}`, result.draft_markdown || "", "update")}>Update learned draft</button>
                    </div>
                    {feedbackStatus && <p className="status">{feedbackStatus}</p>}
                    {learningStatus && <p className="status">{learningStatus}</p>}
                  </div>
                </article>
              )}

            </>
          )}
        </section>
      </section>
          </>
        )}
        <AppFooter copy={copy} onNavigate={navigateToPage} />
      </div>
    </main>
  );
}

function NeuralBackdrop() {
  return (
    <div className="neural-backdrop" aria-hidden="true">
      <span className="neural-line line-a" />
      <span className="neural-line line-b" />
      <span className="neural-line line-c" />
      <span className="neural-node node-a" />
      <span className="neural-node node-b" />
      <span className="neural-node node-c" />
      <span className="neural-node node-d" />
    </div>
  );
}

function ExecutionLogPanel({
  title,
  events,
  compact = false
}: {
  title: string;
  events: ExecutionLogEvent[];
  compact?: boolean;
}) {
  const normalizedEvents = normalizeExecutionEvents(events);
  const visibleEvents = compact ? compactThinkingEvents(normalizedEvents) : normalizedEvents;
  if (compact) {
    const activeEvent = normalizedEvents.find((event) => event.status === "running") || normalizedEvents.find((event) => event.status === "failed" || event.status === "blocked") || normalizedEvents.findLast((event) => event.status === "completed") || normalizedEvents[0];
    if (!activeEvent) {
      return null;
    }
    return (
      <article className="process-indicator">
        <span className={`process-dot ${activeEvent.status}`} />
        <strong>{activeEvent.agent}</strong>
        <small>{activeEvent.phase}</small>
      </article>
    );
  }
  return (
    <article className="execution-log">
      <div className="section-title">
        <h2>{title}</h2>
        <span>{compact ? "thinking" : `${visibleEvents.length} events`}</span>
      </div>
      <div className="execution-list">
        {visibleEvents.map((event, index) => (
          <div className={`execution-event ${event.status}`} key={`${event.agent}-${event.phase}-${index}`}>
            <div className="execution-marker" />
            <div>
              <div className="execution-heading">
                <strong>{event.agent}</strong>
                <span>{event.phase} | {event.status}</span>
              </div>
              <p>{event.message}</p>
              {!compact && event.details && Object.keys(event.details).length > 0 && (
                <details>
                  <summary>Details</summary>
                  <pre>{JSON.stringify(event.details, null, 2)}</pre>
                </details>
              )}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function normalizeExecutionEvents(events: ExecutionLogEvent[]): ExecutionLogEvent[] {
  const latestTerminalByAgent = new Map<string, number>();
  events.forEach((event, index) => {
    if (["completed", "blocked", "failed"].includes(String(event.status))) {
      latestTerminalByAgent.set(`${event.agent}:${event.phase}`, index);
    }
  });
  return events.map((event, index) => {
    const terminalIndex = latestTerminalByAgent.get(`${event.agent}:${event.phase}`);
    if (event.status === "running" && terminalIndex != null && terminalIndex > index) {
      return { ...event, status: "completed", message: `${event.message} Completed.` };
    }
    return event;
  });
}

function compactThinkingEvents(events: ExecutionLogEvent[]): ExecutionLogEvent[] {
  const activeIndex = events.findIndex((event) => event.status === "running" || event.status === "failed" || event.status === "blocked");
  if (activeIndex >= 0) {
    return events.slice(Math.max(0, activeIndex - 2), Math.min(events.length, activeIndex + 3));
  }
  return events.slice(-3);
}

function AppNavbar({
  currentPage,
  user,
  theme,
  setTheme,
  appLanguage,
  setAppLanguage,
  llmProvider,
  copy,
  onNavigate,
  onSignOut
}: {
  currentPage: Page;
  user: UserAccount | null;
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  appLanguage: AppLanguage;
  setAppLanguage: (language: AppLanguage) => void;
  llmProvider: string;
  copy: Record<string, string>;
  onNavigate: (page: Page) => void;
  onSignOut: () => void;
}) {
  function cycleTheme() {
    const order: ThemeMode[] = ["system", "light", "dark"];
    setTheme(order[(order.indexOf(theme) + 1) % order.length]);
  }

  return (
    <header className="app-navbar">
      <button className="brand-mark" onClick={() => onNavigate("workspace")}>
        <img src="/legal-document-ai-icon.png" alt="" />
        <strong>Legal AI Pattern Studio</strong>
      </button>
      <nav>
        <button className={currentPage === "workspace" ? "active" : ""} onClick={() => onNavigate("workspace")}>{copy.workspace}</button>
        <button className={currentPage === "library" ? "active" : ""} onClick={() => onNavigate("library")}>{copy.samples}</button>
        <button className={currentPage === "classifier" ? "active" : ""} onClick={() => onNavigate("classifier")}>{copy.classifier}</button>
        <button className={currentPage === "history" ? "active" : ""} onClick={() => onNavigate("history")}>{copy.history}</button>
        <button className={currentPage === "settings" ? "active" : ""} onClick={() => onNavigate("settings")}>{copy.settings}</button>
        {user?.accountType === "firm" && <button className={currentPage === "admin" ? "active" : ""} onClick={() => onNavigate("admin")}>{copy.admin}</button>}
        <button className={currentPage === "contact" ? "active" : ""} onClick={() => onNavigate("contact")}>{copy.contact}</button>
        <button className={currentPage === "about" ? "active" : ""} onClick={() => onNavigate("about")}>{copy.about}</button>
      </nav>
      <div className="navbar-actions">
        <button className="icon-button" onClick={cycleTheme} title={`Theme: ${theme}`}>
          <ThemeIcon theme={theme} />
        </button>
        <LanguagePicker value={appLanguage} onChange={setAppLanguage} compact />
        <div className="nav-provider">
          <span>{copy.provider}</span>
          <strong>{llmProvider === "mock" ? "Mock LLM" : llmProvider}</strong>
        </div>
        {user ? (
          <>
            <button className="nav-account" onClick={() => onNavigate("profile")} type="button">
              <strong>{user.name}</strong>
              <span>{displayRole(user.role)}</span>
            </button>
            <button className="secondary small" onClick={onSignOut}>{copy.signOut}</button>
          </>
        ) : (
          <>
            <button className={currentPage === "login" ? "secondary small active" : "secondary small"} onClick={() => onNavigate("login")}>{copy.login}</button>
            <button className={currentPage === "signup" ? "primary small active" : "primary small"} onClick={() => onNavigate("signup")}>{copy.signup}</button>
          </>
        )}
      </div>
    </header>
  );
}

function ThemeIcon({ theme }: { theme: ThemeMode }) {
  if (theme === "light") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v3M12 19v3M4.9 4.9 7 7M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1" />
      </svg>
    );
  }
  if (theme === "dark") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 14.5A7.5 7.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </svg>
  );
}

function LanguagePicker({
  value,
  onChange,
  compact = false
}: {
  value: AppLanguage;
  onChange: (language: AppLanguage) => void;
  compact?: boolean;
}) {
  const selected = appLanguages.find((language) => language.code === value) || appLanguages[1];

  return (
    <label className={compact ? "language-select-control compact" : "language-select-control"}>
      <span className="sr-only">App language</span>
      <span className="language-select-inner">
        <img className="flag-image" src={selected.flagSrc} alt="" aria-hidden="true" />
        <select
          aria-label="App language"
          title={`Language: ${selected.label}`}
          value={value}
          onChange={(event) => onChange(event.target.value as AppLanguage)}
        >
          {appLanguages.map((language) => (
            <option key={language.code} value={language.code}>
              {compact ? language.shortLabel : language.label}
            </option>
          ))}
        </select>
      </span>
    </label>
  );
}

function AuthPage({
  mode,
  authDraft,
  setAuthDraft,
  authPassword,
  setAuthPassword,
  authFirmName,
  setAuthFirmName,
  authStatus,
  submitAuth,
  switchMode
}: {
  mode: "login" | "signup";
  authDraft: UserAccount;
  setAuthDraft: (value: UserAccount) => void;
  authPassword: string;
  setAuthPassword: (value: string) => void;
  authFirmName: string;
  setAuthFirmName: (value: string) => void;
  authStatus: string;
  submitAuth: () => void | Promise<void>;
  switchMode: (page: "login" | "signup") => void;
}) {
  const signup = mode === "signup";
  return (
    <section className="auth-page">
      <article className="auth-hero">
        <p className="eyebrow">{signup ? "Prototype account setup" : "Prototype workspace login"}</p>
        <h1>{signup ? "Set up individual or firm access." : "Log in to continue legal drafting."}</h1>
        <p>
          Firm accounts model senior review, junior assignment visibility, and matter-level controls. Individual
          accounts keep drafts private to a single user.
        </p>
        <div className="auth-feature-grid">
          <div><strong>Firm tenancy</strong><span>Separate firm workspaces and matter records.</span></div>
          <div><strong>Role controls</strong><span>Senior lawyers can review assigned junior work.</span></div>
          <div><strong>Review audit</strong><span>Every generated draft keeps trace and QA artifacts.</span></div>
        </div>
      </article>

      <article className="auth-form-card">
        <div className="section-title">
          <h2>{signup ? "Sign up preview" : "Log in preview"}</h2>
          <button className="link-button" onClick={() => switchMode(signup ? "login" : "signup")}>
            {signup ? "Already have an account?" : "Create account"}
          </button>
        </div>
        <label>
          Full name
          <input value={authDraft.name} onChange={(event) => setAuthDraft({ ...authDraft, name: event.target.value })} />
        </label>
        <label>
          Work email
          <input value={authDraft.email} onChange={(event) => setAuthDraft({ ...authDraft, email: event.target.value })} />
        </label>
        <label>
          Password
          <input type="password" value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} placeholder="Enter password" />
        </label>
        {signup && (
          <>
            <div className="two-col">
              <label>
                Account type
                <select value={authDraft.accountType} onChange={(event) => setAuthDraft({ ...authDraft, accountType: event.target.value as UserAccount["accountType"] })}>
                  <option value="individual">Individual</option>
                  <option value="firm">Firm</option>
                </select>
              </label>
              <label>
                Initial role
                <select value={authDraft.role} onChange={(event) => setAuthDraft({ ...authDraft, role: event.target.value as UserAccount["role"] })}>
                  <option value="senior_lawyer">Senior lawyer</option>
                  <option value="junior_lawyer">Junior lawyer</option>
                  <option value="paralegal">Paralegal</option>
                </select>
              </label>
            </div>
            <label>
              Firm name
              <input value={authFirmName} onChange={(event) => setAuthFirmName(event.target.value)} placeholder="Example Legal Partners LLP" />
            </label>
          </>
        )}
        <p className="field-note">
          Authentication is handled by the backend. Production hardening adds SSO, password policy, RBAC,
          firm tenancy, audit logs, and encrypted matter storage.
        </p>
        {authStatus && <p className={authStatus.toLowerCase().includes("failed") ? "error" : "status"}>{authStatus}</p>}
        <button className="primary" onClick={submitAuth}>{signup ? "Create account" : "Log in"}</button>
      </article>
    </section>
  );
}

function DocumentLibraryPage({
  onUsePack,
  onUseTopic
}: {
  onUsePack: (packId: string) => void;
  onUseTopic: (area: string, topic: string) => void;
}) {
  const totalDocuments = legalDocumentCatalog.reduce((total, group) => total + group.documents.length, 0);
  return (
    <section className="library-page">
      <article className="library-hero">
        <p className="eyebrow">Scalable legal document library</p>
        <h1>From two assessment samples to a reusable firm drafting platform.</h1>
        <p>
          The uploaded dismissal and damages samples are starting points. A production legal drafting system should
          organize hundreds of recurring document types by practice area, then reuse the same classifier, pattern
          extraction, retrieval, drafting, validation, citation, and QA workflow.
        </p>
        <p className="field-note">
          Runnable in this prototype: dismissal protection suit, claim for damages, and editable custom sample packs.
          The wider catalog below is a production taxonomy and roadmap, not a claim that every document type is already
          implemented.
        </p>
        <div className="library-stats">
          <Metric label="Practice areas" value={`${legalDocumentCatalog.length}`} />
          <Metric label="Example draft types" value={`${totalDocuments}+`} strong />
          <Metric label="Architecture" value="Reusable agents" />
        </div>
      </article>

      <section className="pack-grid">
        {[
          {
            id: "challenge-dismissal",
            title: "Dismissal protection suit",
            badge: "Challenge data",
            description: "Learns from the provided assessment samples in the dismissal-protection document family."
          },
          {
            id: "challenge-damages",
            title: "Claim for damages",
            badge: "Challenge data",
            description: "Learns from the provided assessment samples for civil or commercial damages claims."
          },
          {
            id: "firm-dismissal",
            title: "Firm dismissal pack",
            badge: "Editable demo pack",
            description: "A small built-in example of how a firm could upload its own approved precedent documents."
          },
          {
            id: "commercial-damages",
            title: "Commercial damages pack",
            badge: "Editable demo pack",
            description: "A custom sample pack showing how the same workflow can draft from commercial dispute examples."
          }
        ].map((pack) => (
          <article className="pack-card" key={pack.id}>
            <span>{pack.badge}</span>
            <h2>{pack.title}</h2>
            <p>{pack.description}</p>
            <button className="secondary" onClick={() => onUsePack(pack.id)}>Open in workspace</button>
          </article>
        ))}
      </section>

      <article className="support-band">
        <div>
          <span>Runnable now</span>
          <strong>2 challenge families + custom uploaded examples</strong>
        </div>
        <div>
          <span>Future scale path</span>
          <strong>Classifier-driven routing across practice areas</strong>
        </div>
        <div>
          <span>Review stance</span>
          <strong>Every generated draft remains lawyer-reviewed</strong>
        </div>
      </article>

      <section className="catalog-grid">
        {legalDocumentCatalog.map((group) => (
          <article className="catalog-card" key={group.area}>
            <div className="section-title">
              <div>
                <h2>{group.area}</h2>
                <p>{group.german}</p>
              </div>
              <span>{group.documents.length} types</span>
            </div>
            <div className="document-chip-list">
              {group.documents.map((document) => {
                const summary = topicFieldSummary(group.area, document);
                const runnable = Boolean(runnableDocumentMap[`${group.area}::${document}`]);
                return (
                  <button
                    className={runnable ? "document-chip runnable" : "document-chip roadmap"}
                    key={document}
                    onClick={() => onUseTopic(group.area, document)}
                    title={`${summary.requiredLabel}: ${summary.required.join(", ")} | ${summary.optionalLabel}: ${summary.optional.join(", ")}`}
                    type="button"
                  >
                    {document}
                    <span className="chip-tooltip">
                      <strong>{runnable ? "Runnable sample" : "Custom roadmap schema"}</strong>
                      <em>{summary.requiredLabel}</em>
                      <small>{summary.required.join(", ")}</small>
                      <em>{summary.optionalLabel}</em>
                      <small>{summary.optional.join(", ")}</small>
                    </span>
                  </button>
                );
              })}
            </div>
          </article>
        ))}
      </section>

    </section>
  );
}

function topicFieldSummary(area: string, topic: string) {
  const packId = runnableDocumentMap[`${area}::${topic}`] || "";
  const backendDocType = builtInPacks.find((pack) => pack.id === packId)?.backendDocType || "custom_legal_documents";
  const fields = fieldsFor(backendDocType, packId);
  const required = fields.filter((field) => field.required).map((field) => field.label);
  const optional = fields.filter((field) => !field.required).map((field) => field.label);
  return {
    requiredLabel: "Required fields",
    optionalLabel: "Optional fields",
    required: required.length ? required : ["Matter or case number", "Client / claimant", "Matter summary"],
    optional: optional.length ? optional : ["Supporting evidence", "Reviewer notes", "Requested relief"]
  };
}

function DocumentClassifierPage({
  documents,
  results,
  coverage,
  status,
  onLoadFiles,
  onAddTextSample,
  onUpdateDocument,
  onClassify,
  onRouteToWorkspace,
  onAddAsSource
}: {
  documents: SourceDocument[];
  results: ClassificationResult[];
  coverage: ClassifierCoverage | null;
  status: string;
  onLoadFiles: (event: ChangeEvent<HTMLInputElement>) => void;
  onAddTextSample: () => void;
  onUpdateDocument: (id: number, patch: Partial<SourceDocument>) => void;
  onClassify: () => void;
  onRouteToWorkspace: (result: ClassificationResult) => void;
  onAddAsSource: (result: ClassificationResult) => void;
}) {
  const totalCatalogTypes = legalDocumentCatalog.reduce((total, group) => total + group.documents.length, 0);
  const mappedTypes = classifierPlatformMappings.length;
  const missingTypes = Math.max(0, totalCatalogTypes - mappedTypes);
  return (
    <section className="classifier-page">
      <article className="library-hero">
        <p className="eyebrow">Document classifier</p>
        <h1>Identify uploaded legal documents, then route them into the drafting workspace.</h1>
        <p>
          Classification is an intake step. It does not draft the document. It decides which practice area and document
          type the uploaded material belongs to, so the platform can select the right sample family, required fields,
          retrieval scope, and template-learning path.
        </p>
        <div className="library-stats">
          <Metric label="Platform catalog" value={`${totalCatalogTypes}+`} />
          <Metric label="Mapped classifier types" value={`${mappedTypes}`} strong />
          <Metric label="Granular types to expand" value={`${missingTypes}`} />
        </div>
      </article>

      <section className="classifier-grid">
        <article className="settings-card">
          <div className="section-title">
            <div>
              <h2>Documents to classify</h2>
              <p>Upload text-like files or paste extracted document text. PDF/DOCX extraction should be handled by the ingestion worker in production.</p>
            </div>
            <span>{documents.length} loaded</span>
          </div>
          <label className="upload-box">
            <strong>Upload documents for classification</strong>
            <input type="file" multiple onChange={onLoadFiles} />
          </label>
          <div className="button-row">
            <button className="secondary" onClick={onAddTextSample}>Paste document text</button>
            <button className="primary" onClick={onClassify}>Classify documents</button>
          </div>
          {status && <p className="status">{status}</p>}
          <div className="classifier-doc-list">
            {documents.map((document) => (
              <article className="classifier-doc" key={document.id}>
                <input value={document.name} onChange={(event) => onUpdateDocument(document.id, { name: event.target.value })} />
                <textarea value={document.content} onChange={(event) => onUpdateDocument(document.id, { content: event.target.value })} />
              </article>
            ))}
            {!documents.length && <p className="field-note">No classifier input loaded yet.</p>}
          </div>
        </article>

        <article className="settings-card">
          <div className="section-title">
            <div>
              <h2>How it links to the platform</h2>
              <p>The classifier output becomes routing metadata for Workspace, Sample Library, RAG filters, and learned source grouping.</p>
            </div>
          </div>
          <div className="classifier-flow">
            {["Upload", "Security scan", "Classify", "User confirms", "Workspace route", "Drafting agents"].map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
          <div className="coverage-list">
            <strong>Current direct mappings</strong>
            {classifierPlatformMappings.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <p>{item.area} / {item.topic}</p>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="classifier-results">
        <article className="settings-card">
          <div className="section-title">
            <div>
              <h2>Classification results</h2>
              <p>Use a result to preselect the Workspace route, or add the document as a source example for template learning.</p>
            </div>
            {coverage && <span>{coverage.direct_platform_mappings} mappings</span>}
          </div>
          {coverage && <p className="field-note">{coverage.note}</p>}
          <div className="result-grid">
            {results.map((result) => (
              <article className="classification-card" key={`${result.index}-${result.filename}`}>
                <span>{result.classifier || "classifier"}</span>
                <h2>{result.topic || result.document_type || "Unknown document"}</h2>
                <p>{result.practice_area || "Unmapped practice area"}</p>
                <div className="classification-meta">
                  <strong>{Math.round(Number(result.confidence || 0) * 100)}%</strong>
                  <small>confidence</small>
                  {result.raw_label && <small>raw label: {result.raw_label}</small>}
                </div>
                {result.status === "blocked" && <p className="error">Security guardrails blocked this document.</p>}
                {result.signals?.length ? <p className="field-note">{result.signals.join(", ")}</p> : null}
                <div className="button-row">
                  <button className="secondary" onClick={() => onRouteToWorkspace(result)}>Open in Workspace</button>
                  <button className="primary" onClick={() => onAddAsSource(result)}>Add as source</button>
                </div>
              </article>
            ))}
            {!results.length && <p className="field-note">Classification results will appear here.</p>}
          </div>
        </article>
      </section>
    </section>
  );
}

function HistoryPage({
  records,
  status,
  onRefresh
}: {
  records: FeedbackRecord[];
  status: string;
  onRefresh: () => void;
}) {
  const positive = records.filter((record) => record.sentiment === "positive");
  const negative = records.filter((record) => record.sentiment === "negative");
  return (
    <section className="history-page">
      <article className="library-hero">
        <p className="eyebrow">Review history</p>
        <h1>Saved generated outputs are grouped by lawyer feedback.</h1>
        <p>
          Positive history can become approved precedent candidates. Negative history is kept separately so the team can
          inspect missing facts, weak retrieval, prompt failures, and legal-review concerns.
        </p>
        <button className="secondary" onClick={onRefresh}>Refresh history</button>
        {status && <p className="status">{status}</p>}
      </article>
      <section className="history-grid">
        <HistoryColumn title="Positive History" records={positive} empty="No positive feedback saved yet." />
        <HistoryColumn title="Negative History" records={negative} empty="No negative feedback saved yet." negative />
      </section>
    </section>
  );
}

function HistoryColumn({
  title,
  records,
  empty,
  negative = false
}: {
  title: string;
  records: FeedbackRecord[];
  empty: string;
  negative?: boolean;
}) {
  return (
    <article className={negative ? "history-column negative" : "history-column"}>
      <div className="section-title">
        <h2>{title}</h2>
        <span>{records.length} saved</span>
      </div>
      {!records.length && <p className="field-note">{empty}</p>}
      {records.map((record) => (
        <div className="history-item" key={record.id}>
          <div>
            <strong>{record.document_type.replaceAll("_", " ") || "Generated draft"}</strong>
            <span>{new Date(record.created_at).toLocaleString()} | Run {record.run_id.slice(-7)}</span>
          </div>
          <p>{record.comment || "No reviewer comment provided."}</p>
          <small>QA {record.qa_score == null ? "n/a" : `${Math.round(record.qa_score * 100)}%`} | Reviewer {record.reviewer}</small>
          <details>
            <summary>Preview saved draft</summary>
            <pre>{record.draft_markdown || "No draft text saved."}</pre>
          </details>
        </div>
      ))}
    </article>
  );
}

function ProfilePage({
  user,
  setUser,
  authToken,
  apiHeaders
}: {
  user: UserAccount | null;
  setUser: (user: UserAccount | null) => void;
  authToken: string;
  apiHeaders: (extra?: Record<string, string>) => Record<string, string>;
}) {
  const [profileDraft, setProfileDraft] = useState<UserAccount>(user || defaultUser);
  const [profileStatus, setProfileStatus] = useState("");
  const [passwordEmail, setPasswordEmail] = useState(user?.email || "");

  if (!user) {
    return (
      <section className="content-page">
        <article className="library-hero">
          <p className="eyebrow">Profile</p>
          <h1>Log in to manage your account profile.</h1>
          <p>Profile, password, email verification, and firm visibility settings require an authenticated account.</p>
        </article>
      </section>
    );
  }

  async function saveProfile() {
    if (!authToken) {
      setProfileStatus("Log in before saving profile settings.");
      return;
    }
    setProfileStatus("Saving profile...");
    try {
      const response = await fetch("/api/profile", {
        method: "PATCH",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(profileDraft)
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Profile could not be saved.");
      }
      setUser(body.user);
      setProfileDraft(body.user);
      setProfileStatus("Profile saved in PostgreSQL.");
    } catch (caught) {
      setProfileStatus(caught instanceof Error ? caught.message : "Profile could not be saved.");
    }
  }

  async function sendEmailVerification() {
    setProfileStatus("Requesting verification email...");
    try {
      const response = await fetch("/api/auth/request-email-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: profileDraft.email })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Verification email could not be requested.");
      }
      setProfileStatus(`Verification email queued for ${profileDraft.email}.`);
    } catch (caught) {
      setProfileStatus(caught instanceof Error ? caught.message : "Verification email could not be requested.");
    }
  }

  async function sendPasswordReset() {
    const email = passwordEmail || profileDraft.email;
    setProfileStatus("Requesting password reset email...");
    try {
      const response = await fetch("/api/auth/request-password-reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Password reset could not be requested.");
      }
      setProfileStatus(`Password reset email queued for ${email}.`);
    } catch (caught) {
      setProfileStatus(caught instanceof Error ? caught.message : "Password reset could not be requested.");
    }
  }

  return (
    <section className="profile-page">
      <article className="library-hero profile-hero">
        <p className="eyebrow">User profile</p>
        <h1>{user.name}</h1>
        <p className="profile-designation">{displayRole(user.role)} | {user.accountType === "firm" ? "Firm account" : "Individual account"}</p>
        <p>Manage profile details, email verification, password-change verification, and account visibility.</p>
      </article>
      <section className="settings-grid">
        <article className="settings-card">
          <h2>Profile Details</h2>
          <div className="two-col">
            <label>
              Full name
              <input value={profileDraft.name} onChange={(event) => setProfileDraft({ ...profileDraft, name: event.target.value })} />
            </label>
            <label>
              Email
              <input value={profileDraft.email} onChange={(event) => setProfileDraft({ ...profileDraft, email: event.target.value })} />
            </label>
            <label>
              Account type
              <select value={profileDraft.accountType} onChange={(event) => setProfileDraft({ ...profileDraft, accountType: event.target.value as UserAccount["accountType"] })}>
                <option value="individual">Individual</option>
                <option value="firm">Firm</option>
              </select>
            </label>
            <label>
              Designation
              <select value={profileDraft.role} onChange={(event) => setProfileDraft({ ...profileDraft, role: event.target.value as UserAccount["role"] })}>
                <option value="senior_lawyer">Senior lawyer</option>
                <option value="junior_lawyer">Junior lawyer</option>
                <option value="paralegal">Paralegal</option>
              </select>
            </label>
          </div>
          <button className="primary" onClick={saveProfile}>Save profile</button>
        </article>
        <article className="settings-card">
          <h2>Security</h2>
          <div className="security-actions">
            <div>
              <strong>Email verification</strong>
              <p className="field-note">Verify account ownership before sharing firm templates or reviewer history.</p>
              <button className="secondary" onClick={sendEmailVerification}>Send verification email</button>
            </div>
            <div>
              <strong>Change password</strong>
              <p className="field-note">Password changes require email verification before the new password is accepted.</p>
              <input value={passwordEmail} onChange={(event) => setPasswordEmail(event.target.value)} placeholder="Email for password verification" />
              <button className="secondary" onClick={sendPasswordReset}>Verify by email</button>
            </div>
          </div>
          {profileStatus && <p className="status">{profileStatus}</p>}
        </article>
      </section>
    </section>
  );
}

function SettingsPage({
  user,
  theme,
  setTheme,
  appLanguage,
  setAppLanguage,
  providerSettings,
  updateProviderSettings,
  legalQuestion,
  setLegalQuestion,
  legalSourceUrls,
  setLegalSourceUrls,
  legalVerification,
  legalVerificationStatus,
  verifyLegalSources,
  saveProviderConfig,
  providerSaveStatus,
  providerConfigs,
  subscriptionInfo,
  subscriptionStatus,
  onRefreshSubscription
}: {
  user: UserAccount | null;
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  appLanguage: AppLanguage;
  setAppLanguage: (language: AppLanguage) => void;
  providerSettings: ProviderSettings;
  updateProviderSettings: (patch: Partial<ProviderSettings>) => void;
  legalQuestion: string;
  setLegalQuestion: (value: string) => void;
  legalSourceUrls: string;
  setLegalSourceUrls: (value: string) => void;
  legalVerification: LegalVerificationResult | null;
  legalVerificationStatus: string;
  verifyLegalSources: () => void;
  saveProviderConfig: () => void | Promise<void>;
  providerSaveStatus: string;
  providerConfigs: Array<{ id: string; provider: string; model: string; base_url: string; scope: string; has_api_key: boolean }>;
  subscriptionInfo: { plan: string; billing_cycle: string; monthly_limit: number; used_count: number; remaining: number } | null;
  subscriptionStatus: string;
  onRefreshSubscription: () => void | Promise<void>;
}) {
  return (
    <section className="settings-page">
      <article className="library-hero">
        <p className="eyebrow">Dashboard settings</p>
        <h1>Control workspace preferences, model provider, and firm access visibility.</h1>
        <p>
          These settings are local prototype controls. Production would persist them per user or firm, enforce them
          through the backend, and audit every change.
        </p>
      </article>
      <section className="settings-grid">
        <article className="settings-card">
          <h2>Appearance</h2>
          <div className="two-col">
            <label>
              Theme
              <select value={theme} onChange={(event) => setTheme(event.target.value as ThemeMode)}>
                <option value="system">System preference</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </label>
            <div className="settings-language">
              <span>App language</span>
              <LanguagePicker value={appLanguage} onChange={setAppLanguage} />
            </div>
          </div>
          <p className="field-note">Keeps the interface readable for long drafting and review sessions.</p>
        </article>
        <article className="settings-card">
          <h2>LLM Provider</h2>
          <div className="two-col">
            <label>
              Provider
              <select value={providerSettings.provider} onChange={(event) => updateProviderSettings({ provider: event.target.value })}>
                <option value="mock">Mock LLM</option>
                <option value="ollama">Ollama</option>
                <option value="openai-compatible">OpenAI-compatible</option>
              </select>
            </label>
            <label>
              Model
              <input value={providerSettings.model} onChange={(event) => updateProviderSettings({ model: event.target.value })} placeholder="llama3.1:8b" />
            </label>
            <label>
              API key
              <input
                type="password"
                value={providerSettings.apiKey}
                onChange={(event) => updateProviderSettings({ apiKey: event.target.value })}
                placeholder="Only sent to backend for this request"
              />
            </label>
            <label>
              Base URL
              <input
                value={providerSettings.baseUrl}
                onChange={(event) => updateProviderSettings({ baseUrl: event.target.value })}
                placeholder="https://api.openai.com/v1 or http://localhost:11434"
              />
            </label>
          </div>
          <div className="button-row">
            <button className="primary" onClick={saveProviderConfig}>Save encrypted provider config</button>
          </div>
          {providerSaveStatus && <p className="status">{providerSaveStatus}</p>}
          {providerConfigs.length > 0 && (
            <div className="saved-config-list">
              {providerConfigs.map((config) => (
                <div key={config.id}>
                  <strong>{config.provider} / {config.model || "default model"}</strong>
                  <span>{config.scope} scope | key {config.has_api_key ? "stored encrypted" : "not stored"} | {config.base_url || "default URL"}</span>
                </div>
              ))}
            </div>
          )}
          <p className="field-note">API keys are encrypted server-side and only metadata is returned to the browser.</p>
        </article>
        <article className="settings-card">
          <h2>Subscription and Usage</h2>
          {subscriptionInfo ? (
            <div className="usage-panel">
              <Metric label="Plan" value={`${subscriptionInfo.plan} / ${subscriptionInfo.billing_cycle}`} />
              <Metric label="Monthly limit" value={`${subscriptionInfo.monthly_limit}`} />
              <Metric label="Used" value={`${subscriptionInfo.used_count}`} />
              <Metric label="Remaining" value={`${subscriptionInfo.remaining}`} strong />
            </div>
          ) : (
            <p className="field-note">{subscriptionStatus || "Log in to see your draft quota."}</p>
          )}
          {subscriptionStatus && subscriptionInfo && <p className="status">{subscriptionStatus}</p>}
          <div className="button-row">
            <button className="secondary" onClick={onRefreshSubscription}>Refresh usage</button>
            <button className="secondary">Stripe checkout placeholder</button>
            <button className="secondary">Paddle checkout placeholder</button>
          </div>
          <p className="field-note">Backend enforces 20 free drafts/month and 50 paid drafts/month before draft generation. Payment buttons need live Stripe or Paddle credentials before production use.</p>
        </article>
        <article className="settings-card">
          <h2>Official Legal Verification</h2>
          <div className="two-col">
            <label>
              Legal country
              <select value={providerSettings.legalCountry} onChange={(event) => updateProviderSettings({ legalCountry: event.target.value })}>
                {legalCountries.map((country) => <option key={country.code} value={country.code}>{country.label}</option>)}
              </select>
            </label>
            <label>
              Draft output language
              <select value={providerSettings.outputLanguage} onChange={(event) => updateProviderSettings({ outputLanguage: event.target.value as AppLanguage })}>
                {appLanguages.map((language) => <option key={language.code} value={language.code}>{language.label}</option>)}
              </select>
            </label>
            <label>
              Verification question
              <input value={legalQuestion} onChange={(event) => setLegalQuestion(event.target.value)} />
            </label>
          </div>
          <label>
            Official source URLs
            <textarea value={legalSourceUrls} onChange={(event) => setLegalSourceUrls(event.target.value)} rows={5} />
          </label>
          <button className="secondary" onClick={verifyLegalSources}>Verify official-source policy</button>
          {legalVerificationStatus && <p className="status">{legalVerificationStatus}</p>}
          {legalVerification && (
            <div className="verification-result">
              <strong>Allowed official domains for {legalVerification.country}</strong>
              <p>{legalVerification.allowed_domains.join(", ")}</p>
              {legalVerification.rejected_sources.length > 0 && (
                <p className="error">Rejected non-official sources: {legalVerification.rejected_sources.map((source) => source.url).join(", ")}</p>
              )}
              <small>{legalVerification.instruction}</small>
            </div>
          )}
        </article>
      </section>
      <AccessPanel user={user} />
      <article className="support-band">
        <div>
          <span>Individual account</span>
          <strong>Private drafts and personal matter history</strong>
        </div>
        <div>
          <span>Firm account</span>
          <strong>Senior review, junior assignments, shared template approval</strong>
        </div>
        <div>
          <span>Production requirement</span>
          <strong>Server-enforced RBAC, SSO, and immutable audit trail</strong>
        </div>
      </article>
    </section>
  );
}

function ContactPage({
  user,
  authToken,
  apiHeaders
}: {
  user: UserAccount | null;
  authToken: string;
  apiHeaders: (extra?: Record<string, string>) => Record<string, string>;
}) {
  const [contactEmail, setContactEmail] = useState(user?.email || "");
  const [contactSubject, setContactSubject] = useState("Product support request");
  const [contactMessage, setContactMessage] = useState("");
  const [contactStatus, setContactStatus] = useState("");
  const [chatCategory, setChatCategory] = useState<"chatbot" | "complaint" | "support">("chatbot");
  const [chatMessage, setChatMessage] = useState("");
  const [chatLog, setChatLog] = useState<Array<{ role: "user" | "assistant"; text: string; ticket?: string }>>([
    {
      role: "assistant",
      text: "Ask me how to use the drafting workspace, or report a complaint and I will create a support ticket."
    }
  ]);

  async function sendContact() {
    setContactStatus("Creating support ticket...");
    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_email: contactEmail || user?.email || "guest@example.com",
          subject: contactSubject,
          message: contactMessage,
          category: "support"
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Ticket could not be created.");
      }
      setContactStatus(`Ticket ${body.ticket.ticket_no} created and routed to the development team.`);
      setContactMessage("");
    } catch (caught) {
      setContactStatus(caught instanceof Error ? caught.message : "Ticket could not be created.");
    }
  }

  async function sendChat() {
    if (!chatMessage.trim()) {
      return;
    }
    const outgoing = chatMessage.trim();
    setChatLog((current) => [...current, { role: "user", text: outgoing }]);
    setChatMessage("");
    try {
      const response = await fetch("/api/chatbot/message", {
        method: "POST",
        headers: apiHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          user_email: user?.email || contactEmail || "guest@example.com",
          message: outgoing,
          category: chatCategory
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(body.detail || "Chatbot request failed.");
      }
      setChatLog((current) => [
        ...current,
        { role: "assistant", text: body.reply, ticket: body.ticket?.ticket_no }
      ]);
    } catch (caught) {
      setChatLog((current) => [
        ...current,
        { role: "assistant", text: caught instanceof Error ? caught.message : "Chatbot request failed." }
      ]);
    }
  }

  return (
    <section className="contact-page">
      <article className="library-hero">
        <p className="eyebrow">Contact us</p>
        <h1>Reach support, report issues, or ask the AI assistant how to use the app.</h1>
        <p>
          Support requests and chatbot complaints are saved as tickets so a representative or development team can
          review the record later.
        </p>
      </article>
      <section className="contact-grid">
        <article className="settings-card">
          <h2>Support Form</h2>
          <label>
            Email
            <input value={contactEmail} onChange={(event) => setContactEmail(event.target.value)} placeholder="name@firm.com" />
          </label>
          <label>
            Subject
            <input value={contactSubject} onChange={(event) => setContactSubject(event.target.value)} />
          </label>
          <label>
            Message
            <textarea value={contactMessage} onChange={(event) => setContactMessage(event.target.value)} rows={7} />
          </label>
          <button className="primary" onClick={sendContact}>Create ticket</button>
          {contactStatus && <p className="status">{contactStatus}</p>}
        </article>
        <article className="settings-card chatbot-card">
          <h2>AI Help Chatbot</h2>
          <div className="chat-log">
            {chatLog.map((item, index) => (
              <div className={item.role === "assistant" ? "chat-message assistant" : "chat-message user"} key={`${item.role}-${index}`}>
                <p>{item.text}</p>
                {item.ticket && <small>Ticket: {item.ticket}</small>}
              </div>
            ))}
          </div>
          <div className="two-col">
            <label>
              Request type
              <select value={chatCategory} onChange={(event) => setChatCategory(event.target.value as "chatbot" | "complaint" | "support")}>
                <option value="chatbot">How-to guidance</option>
                <option value="support">Support question</option>
                <option value="complaint">Complaint</option>
              </select>
            </label>
            <label>
              Message
              <input value={chatMessage} onChange={(event) => setChatMessage(event.target.value)} onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void sendChat();
                }
              }} placeholder="How do I generate a draft?" />
            </label>
          </div>
          <button className="secondary" onClick={sendChat}>Send to assistant</button>
          {!authToken && <p className="field-note">Guest chats are saved with the provided email; logged-in users keep tickets in their account scope.</p>}
        </article>
      </section>
    </section>
  );
}

function FirmAdminPage({
  user,
  overview,
  status,
  onRefresh,
  onInvite,
  onAssign
}: {
  user: UserAccount | null;
  overview: Record<string, unknown> | null;
  status: string;
  onRefresh: () => void | Promise<void>;
  onInvite: (email: string, role: UserAccount["role"]) => void | Promise<void>;
  onAssign: (matter: string, email: string, documentType: string) => void | Promise<void>;
}) {
  const [inviteEmail, setInviteEmail] = useState("junior.associate@example.com");
  const [inviteRole, setInviteRole] = useState<UserAccount["role"]>("junior_lawyer");
  const [matterTitle, setMatterTitle] = useState("DPS-2026-014");
  const [assigneeEmail, setAssigneeEmail] = useState("junior.associate@example.com");
  const [documentType, setDocumentType] = useState("Dismissal Protection Suit");
  const users = (overview?.users as Array<Record<string, string>> | undefined) || [];
  const queue = (overview?.review_queue as Array<Record<string, string>> | undefined) || [];
  const assignments = (overview?.assignments as Array<Record<string, string>> | undefined) || [];

  if (!user) {
    return (
      <section className="content-page">
        <article className="library-hero">
          <p className="eyebrow">Firm admin</p>
          <h1>Log in with a firm account to manage users, assignments, and review queues.</h1>
        </article>
      </section>
    );
  }

  return (
    <section className="settings-page">
      <article className="library-hero">
        <p className="eyebrow">Firm admin</p>
        <h1>Manage firm users, matter assignments, senior review, and junior visibility.</h1>
        <p>{String(overview?.visibility_rule || "Senior users can review junior work; juniors only see assigned matters.")}</p>
        <button className="secondary" onClick={onRefresh}>Refresh admin data</button>
        {status && <p className="status">{status}</p>}
      </article>
      <section className="settings-grid">
        <article className="settings-card">
          <h2>Invite User</h2>
          <div className="two-col">
            <label>Email<input value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} /></label>
            <label>Role
              <select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as UserAccount["role"])}>
                <option value="junior_lawyer">Junior lawyer</option>
                <option value="paralegal">Paralegal</option>
                <option value="senior_lawyer">Senior lawyer</option>
              </select>
            </label>
          </div>
          <button className="primary" onClick={() => onInvite(inviteEmail, inviteRole)}>Send invite</button>
        </article>
        <article className="settings-card">
          <h2>Assign Matter</h2>
          <label>Matter<input value={matterTitle} onChange={(event) => setMatterTitle(event.target.value)} /></label>
          <div className="two-col">
            <label>Assignee<input value={assigneeEmail} onChange={(event) => setAssigneeEmail(event.target.value)} /></label>
            <label>Document type<input value={documentType} onChange={(event) => setDocumentType(event.target.value)} /></label>
          </div>
          <button className="primary" onClick={() => onAssign(matterTitle, assigneeEmail, documentType)}>Assign to junior</button>
        </article>
      </section>
      <section className="admin-grid">
        <AdminList title="Firm Users" rows={users} />
        <AdminList title="Senior Review Queue" rows={queue} />
        <AdminList title="Assignments" rows={assignments} />
      </section>
    </section>
  );
}

function AdminList({ title, rows }: { title: string; rows: Array<Record<string, string>> }) {
  return (
    <article className="settings-card">
      <div className="section-title">
        <h2>{title}</h2>
        <span>{rows.length} records</span>
      </div>
      {!rows.length && <p className="field-note">No records yet.</p>}
      {rows.map((row, index) => (
        <div className="admin-row" key={`${title}-${index}`}>
          {Object.entries(row).map(([key, value]) => (
            <span key={key}><strong>{key.replaceAll("_", " ")}</strong>{value}</span>
          ))}
        </div>
      ))}
    </article>
  );
}

function AboutPage() {
  return (
    <section className="content-page">
      <article className="library-hero">
        <p className="eyebrow">About us</p>
        <h1>Legal AI Pattern Drafting Studio helps firms turn precedent examples into reviewed legal drafts.</h1>
        <p>
          The product concept focuses on learning reusable structure from a firm's past work, retrieving relevant source
          language, drafting from new case facts, and routing the result through quality checks and lawyer review.
        </p>
      </article>
      <section className="catalog-grid">
        {[
          ["Pattern learning", "Separate recurring legal structure from matter-specific variables."],
          ["Grounded drafting", "Use retrieved precedent clauses and case facts instead of ungrounded drafting."],
          ["Review workflow", "Keep generated work inside human approval, traceability, and QA controls."],
          ["Production direction", "Move toward server-side RBAC, prompt versioning, observability, and secure document ingestion."]
        ].map(([title, text]) => (
          <article className="catalog-card" key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>
    </section>
  );
}

function CareersPage() {
  return (
    <section className="content-page">
      <article className="library-hero">
        <p className="eyebrow">Careers</p>
        <h1>Build practical legal AI with strong engineering judgment and lawyer-in-the-loop safeguards.</h1>
        <p>
          This prototype represents the kind of work a legal AI team needs: reliable orchestration, grounded LLM output,
          secure document handling, and interfaces that make review easier for legal professionals.
        </p>
      </article>
      <section className="pack-grid">
        {[
          ["AI Engineer", "Agents, retrieval, prompt/version control, schema validation, and evaluation loops."],
          ["Product Engineer", "Drafting workspace, upload flows, review UX, and role-aware dashboards."],
          ["Legal AI Specialist", "Template quality, legal validation rubrics, citation checks, and firm rollout."]
        ].map(([title, text]) => (
          <article className="pack-card" key={title}>
            <span>Example role</span>
            <h2>{title}</h2>
            <p>{text}</p>
            <button className="secondary">Save role</button>
          </article>
        ))}
      </section>
    </section>
  );
}

function PrivacyPolicyPage() {
  return (
    <section className="content-page">
      <article className="library-hero">
        <p className="eyebrow">Privacy policy</p>
        <h1>Privacy-first legal AI drafting starts with clear data boundaries.</h1>
        <p>
          This prototype keeps privacy guidance explicit: legal documents may contain sensitive personal and commercial
          information, so production use should require encryption, access control, audit trails, retention rules, and
          human approval before sharing or exporting matter data.
        </p>
      </article>
      <section className="catalog-grid">
        {[
          ["Data handled", "Case facts, precedent samples, generated drafts, agent traces, QA results, and review notes."],
          ["Prototype storage", "Generated outputs are written locally for demonstration and debugging. No production data-retention guarantees are implied."],
          ["Production controls", "Tenant isolation, role-based access, encrypted storage, deletion workflows, and immutable audit logs would be required."],
          ["LLM usage", "External model providers should receive only the minimum necessary context, with PII redaction and provider-specific data-processing terms."]
        ].map(([title, text]) => (
          <article className="catalog-card" key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>
    </section>
  );
}

function LegalInfoPage({ kind }: { kind: "terms" | "impressum" | "gdpr" }) {
  const content = {
    terms: {
      eyebrow: "Terms of service",
      title: "Legal AI drafts are assistance tools and require qualified lawyer review before use.",
      items: [
        ["No legal advice by the platform", "The system drafts and validates support material, but final legal judgment remains with qualified lawyers."],
        ["Human approval required", "Generated drafts, citations, and retrieved sources must be reviewed before filing, sending, or relying on them."],
        ["Acceptable use", "Users must not upload unlawful data, bypass access controls, or use another country law setting to mislead clients."],
        ["Auditability", "Generation, feedback, provider settings, MCP calls, and support tickets are logged for security and quality review."]
      ]
    },
    impressum: {
      eyebrow: "Impressum / legal notice",
      title: "Production deployment should publish responsible operator, address, contact, and regulatory details.",
      items: [
        ["Operator", "Replace this prototype notice with the legal entity operating the service."],
        ["Contact", "Provide support email, business address, and responsible person for legal notices."],
        ["Professional rules", "For German law firm use, list relevant bar association and professional regulations where applicable."],
        ["Dispute resolution", "Add consumer or business dispute-resolution statements required for the deployment jurisdiction."]
      ]
    },
    gdpr: {
      eyebrow: "GDPR and data processing",
      title: "Legal drafting data needs tenant isolation, minimization, retention rules, and processor controls.",
      items: [
        ["Data categories", "Matter facts, legal documents, generated drafts, QA traces, feedback, account records, and support tickets."],
        ["Lawful basis", "Production deployment must define controller/processor roles and lawful basis for each tenant workflow."],
        ["Data subject rights", "Support access, correction, export, deletion, retention holds, and audit logs."],
        ["Subprocessors", "List LLM providers, hosting, email, payment, analytics, and storage subprocessors with DPAs."]
      ]
    }
  }[kind];

  return (
    <section className="content-page">
      <article className="library-hero">
        <p className="eyebrow">{content.eyebrow}</p>
        <h1>{content.title}</h1>
      </article>
      <section className="catalog-grid">
        {content.items.map(([title, text]) => (
          <article className="catalog-card" key={title}>
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>
    </section>
  );
}

function AppFooter({ copy, onNavigate }: { copy: Record<string, string>; onNavigate: (page: Page) => void }) {
  return (
    <footer className="app-footer">
      <span>Legal AI Pattern Drafting Studio</span>
      <button className="footer-link" onClick={() => onNavigate("privacy")}>{copy.privacy}</button>
      <button className="footer-link" onClick={() => onNavigate("terms")}>{copy.terms}</button>
      <button className="footer-link" onClick={() => onNavigate("impressum")}>{copy.impressum}</button>
      <button className="footer-link" onClick={() => onNavigate("gdpr")}>{copy.gdpr}</button>
      <button className="footer-link" onClick={() => onNavigate("contact")}>{copy.contact}</button>
      <button className="footer-link" onClick={() => onNavigate("careers")}>{copy.careers}</button>
      <span>{copy.lawyerReviewRequired}</span>
      <span>PII-aware drafting, traceable QA, firm access controls</span>
    </footer>
  );
}

function FieldInput({ field, value, onChange }: { field: FieldDef; value: string; onChange: (key: string, value: string) => void }) {
  return (
    <label className={field.required ? "required-field" : ""}>
      {field.label}
      {field.type === "select" ? (
        <select value={value} onChange={(event) => onChange(field.key, event.target.value)}>
          <option value="">Select...</option>
          {(field.options || []).map((option) => <option value={option} key={option}>{option}</option>)}
        </select>
      ) : (
        <input value={value} onChange={(event) => onChange(field.key, event.target.value)} placeholder={field.type === "money" ? "EUR 0.00" : undefined} />
      )}
    </label>
  );
}

function Metric({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <article className={strong ? "metric strong" : "metric"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function AccessStrip({ user, onOpenAccess }: { user: UserAccount | null; onOpenAccess: () => void }) {
  return (
    <div className="access-strip">
      <div>
        <span>Access model</span>
        <strong>{user ? `${displayRole(user.role)} - ${user.accountType}` : "Guest workspace"}</strong>
      </div>
      <button className="secondary small" onClick={onOpenAccess}>View permissions</button>
    </div>
  );
}

function AccessPanel({ user }: { user: UserAccount | null }) {
  if (!user) {
    return (
      <article className="review-card">
        <h2>Guest Access</h2>
        <p>Guest users can test drafting, but saved matters, assignments, and firm visibility require an account.</p>
      </article>
    );
  }

  const senior = user.role === "senior_lawyer";
  return (
    <article className="review-card access-panel">
      <h2>{user.accountType === "firm" ? "Firm Workspace Permissions" : "Individual Workspace"}</h2>
      <div className="permission-grid">
        <div>
          <span>Current role</span>
          <strong>{displayRole(user.role)}</strong>
          <p>{senior ? "Can review junior work, assign matters, and publish approved templates." : "Can only see assigned matters and own drafts."}</p>
        </div>
        <div>
          <span>Visibility rule</span>
          <strong>{senior ? "Senior review enabled" : "Assigned-work only"}</strong>
          <p>Senior work is hidden from junior users unless a senior explicitly assigns or shares it.</p>
        </div>
      </div>
      <div className="matter-table">
        <div><strong>Matter</strong><strong>Owner</strong><strong>Status</strong></div>
        <div><span>DPS-2024-999</span><span>{senior ? "Junior Associate" : user.name}</span><span>Draft ready for review</span></div>
        <div><span>CFD-2024-999</span><span>Senior Lawyer</span><span>{senior ? "Visible" : "Hidden until assigned"}</span></div>
      </div>
    </article>
  );
}

function fieldsFor(docType: string, packId: string): FieldDef[] {
  if (docType === "claims_for_damages" || packId === "commercial-damages") {
    return damagesFields;
  }
  if (docType === "custom_legal_documents" && packId !== "firm-dismissal") {
    return customFields;
  }
  return dismissalFields;
}

function parseLooseKeyValues(text: string): Record<string, string> {
  const result: Record<string, string> = {};
  text.split(/\r?\n/).forEach((line) => {
    const match = line.match(/^\s*([a-zA-Z0-9_ ]+)\s*[:=]\s*(.+?)\s*$/);
    if (match) {
      result[match[1].trim().toLowerCase().replaceAll(" ", "_")] = match[2].trim();
    }
  });
  return result;
}

function stringRecord(value: unknown): Record<string, string> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, String(item ?? "")]));
}

function displayRole(role: UserAccount["role"]) {
  return role.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function normalizeClassifierTopic(area: string, topic: string) {
  const group = legalDocumentCatalog.find((item) => item.area === area);
  if (!group) {
    return topic;
  }
  if (group.documents.includes(topic)) {
    return topic;
  }
  const lowerTopic = topic.toLowerCase();
  const match = group.documents.find((document) => lowerTopic.includes(document.toLowerCase()) || document.toLowerCase().includes(lowerTopic));
  return match || group.documents[0];
}
