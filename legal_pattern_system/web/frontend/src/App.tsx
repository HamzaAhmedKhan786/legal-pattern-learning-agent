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
  human_review?: {
    status?: string;
    review_required?: boolean;
    qa_score?: number;
    review_reasons?: string[];
  };
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
  name: string;
  email: string;
  accountType: "individual" | "firm";
  role: "senior_lawyer" | "junior_lawyer" | "paralegal";
};

type SamplePack = {
  id: string;
  label: string;
  backendDocType: string;
  description: string;
  caseData: Record<string, string>;
  sourceDocuments?: SourceDocument[];
};

type Page = "workspace" | "login" | "signup" | "library" | "settings" | "about" | "careers" | "privacy";
type ThemeMode = "system" | "light" | "dark";
type AppLanguage = "DE" | "EN" | "ES" | "FR" | "IT";

const appLanguages: Array<{ code: AppLanguage; flagClass: string; label: string }> = [
  { code: "DE", flagClass: "flag-de", label: "Deutsch" },
  { code: "EN", flagClass: "flag-gb", label: "English" },
  { code: "ES", flagClass: "flag-es", label: "Spanish" },
  { code: "FR", flagClass: "flag-fr", label: "French" },
  { code: "IT", flagClass: "flag-it", label: "Italian" }
];

const uiCopy: Record<AppLanguage, Record<string, string>> = {
  EN: {
    workspace: "Workspace",
    samples: "Samples",
    settings: "Settings",
    about: "About",
    careers: "Careers",
    privacy: "Privacy",
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
    settings: "Einstellungen",
    about: "Uber uns",
    careers: "Karriere",
    privacy: "Datenschutz",
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
    settings: "Ajustes",
    about: "Acerca",
    careers: "Carreras",
    privacy: "Privacidad",
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
    settings: "Reglages",
    about: "A propos",
    careers: "Carrieres",
    privacy: "Confidentialite",
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
    settings: "Impostazioni",
    about: "Chi siamo",
    careers: "Carriere",
    privacy: "Privacy",
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

const defaultUser: UserAccount = {
  name: "Hamza Khan",
  email: "hamza@example.com",
  accountType: "firm",
  role: "senior_lawyer"
};

const pagePaths: Record<Page, string> = {
  workspace: "/",
  login: "/login",
  signup: "/signup",
  library: "/library",
  settings: "/settings",
  about: "/about-us",
  careers: "/careers",
  privacy: "/privacy-policy"
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
  if (normalized === "/settings" || normalized === "/access") {
    return "settings";
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
  const [caseData, setCaseData] = useState<Record<string, string>>(dismissalCaseData);
  const [sourceDocuments, setSourceDocuments] = useState<SourceDocument[]>(starterSourceDocuments);
  const [userPrompt, setUserPrompt] = useState("Draft in a formal court-ready style. Keep factual assertions separate from lawyer-review assumptions.");
  const [result, setResult] = useState<AgentRun | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState<"draft" | "trace" | "review">("draft");
  const [currentPage, setCurrentPage] = useState<Page>(() => pageFromPath(window.location.pathname));
  const [user, setUser] = useState<UserAccount | null>(() => {
    const initialPage = pageFromPath(window.location.pathname);
    return initialPage === "login" || initialPage === "signup" ? null : defaultUser;
  });
  const [authDraft, setAuthDraft] = useState<UserAccount>(defaultUser);

  const activeDocType = mode === "built-in" ? selectedPack.backendDocType : "custom_legal_documents";
  const copy = uiCopy[appLanguage];
  const activeFields = fieldsFor(activeDocType, selectedPack.id);
  const missingRequired = activeFields.filter((field) => field.required && !String(caseData[field.key] || "").trim());
  const sourceDocumentsToSend = mode === "custom" ? sourceDocuments : selectedPack.sourceDocuments;

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
    const titles: Record<Page, string> = {
      workspace: "Legal AI Pattern Drafting Studio",
      login: "Login | Legal AI Pattern Drafting Studio",
      signup: "Signup | Legal AI Pattern Drafting Studio",
      library: "Sample Library | Legal AI Pattern Drafting Studio",
      settings: "Settings | Legal AI Pattern Drafting Studio",
      about: "About Us | Legal AI Pattern Drafting Studio",
      careers: "Careers | Legal AI Pattern Drafting Studio",
      privacy: "Privacy Policy | Legal AI Pattern Drafting Studio"
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

  function applyTopicSelection(area: string, topic: string) {
    const packId = runnableDocumentMap[`${area}::${topic}`];
    if (packId) {
      applySamplePack(packId);
      setMode("built-in");
    } else {
      setMode("custom");
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
    setStatus("Learning patterns, grounding clauses, and preparing the draft...");

    const payload = {
      doc_type: activeDocType,
      llm_provider: llmProvider,
      model: model || undefined,
      case_data: {
        ...caseData,
        user_prompt: userPrompt,
        requested_by: user?.email || "guest",
        account_scope: user?.accountType || "guest",
        reviewer_visibility: user?.role === "junior_lawyer" ? "assigned_senior_only" : "firm_senior_review"
      },
      source_documents: sourceDocumentsToSend?.map(({ name, content }) => ({ name, content }))
    };

    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Draft generation failed.");
      }

      setResult(await response.json());
      setActiveView("draft");
      setStatus("");
    } catch (caught) {
      setStatus("");
      setError(caught instanceof Error ? caught.message : "Draft generation failed.");
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
    }
  }

  function submitAuth() {
    setUser(authDraft);
    navigateToPage("workspace");
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
          setUser(null);
          navigateToPage("login");
        }}
      />
      <div className="page-content">
        {currentPage === "login" || currentPage === "signup" ? (
          <AuthPage
            mode={currentPage}
            authDraft={authDraft}
            setAuthDraft={setAuthDraft}
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
          />
        ) : currentPage === "settings" ? (
          <SettingsPage
            user={user}
            theme={theme}
            setTheme={setTheme}
            appLanguage={appLanguage}
            setAppLanguage={setAppLanguage}
            llmProvider={llmProvider}
            setLlmProvider={setLlmProvider}
            model={model}
            setModel={setModel}
          />
        ) : currentPage === "about" ? (
          <AboutPage />
        ) : currentPage === "careers" ? (
          <CareersPage />
        ) : currentPage === "privacy" ? (
          <PrivacyPolicyPage />
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
            </div>
            <button className="primary" disabled={Boolean(status)} onClick={generateDraft}>
              {status ? "Generating..." : "Generate draft"}
            </button>
            {status && <p className="status">{status}</p>}
            {error && <p className="error">{error}</p>}
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
                  <pre>{result.draft_markdown || "Draft artifact was not returned by the backend."}</pre>
                </article>
              )}

              {activeView === "trace" && (
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
              )}

              {activeView === "review" && (
                <article className="review-card">
                  <h2>Lawyer Review Packet</h2>
                  <p>Status: {result.human_review?.status || "pending_lawyer_review"}</p>
                  <p>Trace: {result.trace_dir}</p>
                  <ul>
                    {(result.human_review?.review_reasons || [
                      "Generated legal document requires qualified lawyer review.",
                      "Grounding and citations should be checked before filing."
                    ]).map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
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
        <button className={currentPage === "settings" ? "active" : ""} onClick={() => onNavigate("settings")}>{copy.settings}</button>
        <button className={currentPage === "about" ? "active" : ""} onClick={() => onNavigate("about")}>{copy.about}</button>
        <button className={currentPage === "careers" ? "active" : ""} onClick={() => onNavigate("careers")}>{copy.careers}</button>
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
            <div className="nav-account">
              <span>{displayRole(user.role)}</span>
              <strong>{user.name}</strong>
            </div>
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
  return (
    <div className={compact ? "language-picker compact" : "language-picker"} aria-label="App language">
      {appLanguages.map((language) => (
        <button
          className={value === language.code ? "active" : ""}
          key={language.code}
          onClick={() => onChange(language.code)}
          title={language.label}
          type="button"
        >
          <FlagIcon className={language.flagClass} />
          {!compact && <span>{language.label}</span>}
        </button>
      ))}
    </div>
  );
}

function FlagIcon({ className }: { className: string }) {
  return <span className={`flag-icon ${className}`} aria-hidden="true" />;
}

function AuthPage({
  mode,
  authDraft,
  setAuthDraft,
  submitAuth,
  switchMode
}: {
  mode: "login" | "signup";
  authDraft: UserAccount;
  setAuthDraft: (value: UserAccount) => void;
  submitAuth: () => void;
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
          <input type="password" placeholder="Prototype password field" />
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
              <input placeholder="Example Legal Partners LLP" />
            </label>
          </>
        )}
        <p className="field-note">
          Prototype only: this uses local mock authentication. Production would add SSO, password policy, RBAC,
          firm tenancy, audit logs, and encrypted matter storage.
        </p>
        <button className="primary" onClick={submitAuth}>{signup ? "Create account" : "Log in"}</button>
      </article>
    </section>
  );
}

function DocumentLibraryPage({ onUsePack }: { onUsePack: (packId: string) => void }) {
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
              {group.documents.map((document) => <span key={document}>{document}</span>)}
            </div>
          </article>
        ))}
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
  llmProvider,
  setLlmProvider,
  model,
  setModel
}: {
  user: UserAccount | null;
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  appLanguage: AppLanguage;
  setAppLanguage: (language: AppLanguage) => void;
  llmProvider: string;
  setLlmProvider: (provider: string) => void;
  model: string;
  setModel: (model: string) => void;
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
          </div>
          <p className="field-note">The workspace generation form uses these same provider values.</p>
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

function AppFooter({ copy, onNavigate }: { copy: Record<string, string>; onNavigate: (page: Page) => void }) {
  return (
    <footer className="app-footer">
      <span>Legal AI Pattern Drafting Studio</span>
      <button className="footer-link" onClick={() => onNavigate("privacy")}>{copy.privacy}</button>
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
