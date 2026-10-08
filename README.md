# Paavai Smart Campus AI — Intelligent Academic Portal

A production-quality, responsive AI-powered smart campus web application built for **Paavai Institutions**. Designed around three core pillars:
1. **Unified Information & Communication**: Centralized, real-time official notices and circulars.
2. **Smart Grievance Resolution**: Real-time AI auto-triage (category, priority, department extraction) with lifecycle tracking.
3. **Verified College AI Assistant**: Strict RAG-grounded responses citing official college circulars with confidence indicators.

---

## Architecture & Tech Stack

- **Frontend**: React 19, TypeScript, Vite
- **Styling**: Tailwind CSS (custom modern SaaS design tokens, glassmorphism, responsive navigation)
- **Routing**: React Router DOM (Role-protected routes, mobile bottom nav, desktop sidebar)
- **State & Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Centralized Axios client (`apiClient.ts`) with request/response interceptors & token injection
- **Visual Analytics**: Recharts (Department-wise grievances, resolution velocity SLA charts, inquiry trends)
- **Iconography**: Lucide React
- **Resilience**: Smart mock fallback storage with `localStorage` persistence when backend is offline

---

## Folder Structure

```
paavai-smartcampus-ai/
├── .env                              # Environment configuration (VITE_API_BASE_URL)
├── .env.example
├── index.html                        # Google Fonts (Inter & Outfit), SVG Brand favicon
├── tailwind.config.js                # Custom SaaS palette & animations
├── vite.config.ts                    # Path aliases (@/* -> ./src/*)
├── src/
│   ├── api/                          # Centralized API service layer
│   │   ├── apiClient.ts              # Centralized Axios client with interceptors
│   │   ├── mockStorage.ts            # Persistent offline fallback & NLP classifier
│   │   ├── authApi.ts                # Authentication & demo role switcher
│   │   ├── studentApi.ts             # Student metrics, deadlines & requests
│   │   ├── facultyApi.ts             # Faculty dashboard, approvals & notices
│   │   ├── adminApi.ts               # Admin analytics & system queries
│   │   ├── aiApi.ts                  # Campus assistant RAG & grievance NLP triage
│   │   ├── grievanceApi.ts           # Tickets CRUD & timeline milestone management
│   │   ├── announcementApi.ts        # Broadcast circulars & read state
│   │   ├── opportunityApi.ts         # Hackathons, internships & placement jobs
│   │   └── documentApi.ts            # RAG Document Knowledge Base pipeline
│   ├── types/                        # Strict TypeScript interfaces
│   │   ├── auth.ts                   # User, Role, Credentials
│   │   ├── grievance.ts              # Grievance, Priority, Department, TimelineItem
│   │   ├── ai.ts                     # AIQueryResponse, Citations, ChatMessage
│   │   ├── announcement.ts           # Announcement, AnnouncementCategory
│   │   ├── opportunity.ts            # Opportunity, MatchDetails
│   │   └── document.ts               # KnowledgeDocument, DocumentStatus
│   ├── context/                      # React Context providers
│   │   ├── AuthContext.tsx           # Session management & 1-click role switcher
│   │   └── ToastContext.tsx          # Animated notification toasts
│   ├── hooks/                        # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useToast.ts
│   │   └── useDebounce.ts            # Debouncing for real-time AI typing detection
│   ├── data/
│   │   └── mockData.ts               # High-fidelity realistic Paavai dataset
│   ├── components/
│   │   ├── common/                   # Reusable UI component library
│   │   │   ├── Button.tsx            # Variants, sizes & loading states
│   │   │   ├── Input.tsx             # Accessible Input, Textarea & Select
│   │   │   ├── Badge.tsx             # Status, Priority & Verification badges
│   │   │   ├── Card.tsx              # Elevated SaaS cards with glassmorphism
│   │   │   ├── Modal.tsx             # Accessible backdrop-blurred modal dialogs
│   │   │   ├── Skeleton.tsx          # Loading skeletons
│   │   │   ├── EmptyState.tsx        # Styled empty states with callouts
│   │   │   ├── ErrorState.tsx        # Network/API failure recovery states
│   │   │   └── ProtectedRoute.tsx    # Role-based route authorization
│   │   ├── layout/                   # Application shell
│   │   │   ├── AppLayout.tsx         # Responsive layout orchestrator
│   │   │   ├── Sidebar.tsx           # Desktop sidebar with active role switcher
│   │   │   ├── Header.tsx            # Search, AI launcher, role dropdown
│   │   │   └── MobileNav.tsx         # Mobile bottom navigation bar
│   │   ├── student/
│   │   │   ├── SmartGrievanceModal.tsx # Debounced AI auto-triage preview modal
│   │   │   ├── GrievanceDetailModal.tsx # Progress stepper & audit timeline
│   │   │   ├── OpportunityCard.tsx   # Match % and "Why recommended" breakdown
│   │   │   └── AnnouncementCard.tsx  # Circular viewer & priority badge
│   │   ├── faculty/
│   │   │   └── GrievanceActionModal.tsx # Assign & status transition modal
│   │   └── admin/
│   │       └── DocumentUploadModal.tsx # RAG Knowledge Base document ingestion
│   └── pages/
│       ├── auth/
│       │   └── LoginPage.tsx         # Login with 1-click test evaluation profiles
│       ├── student/
│       │   ├── StudentDashboard.tsx
│       │   ├── StudentAIAssistant.tsx # Perplexity-style verified RAG assistant
│       │   ├── StudentGrievances.tsx
│       │   ├── StudentAnnouncements.tsx
│       │   └── StudentOpportunities.tsx
│       ├── faculty/
│       │   └── FacultyDashboard.tsx
│       └── admin/
│           ├── AdminDashboard.tsx    # Recharts metrics & resolution SLAs
│           ├── AdminDocuments.tsx    # Document Knowledge Base UI
│           ├── AdminGrievances.tsx   # All grievances triage
│           ├── AdminUsers.tsx        # User & Identity directory
│           ├── AdminDepartments.tsx  # Department workload tracking
│           ├── AdminAnnouncements.tsx# Campus-wide broadcasts
│           ├── AdminEvents.tsx       # Symposia & Hackathon calendar
│           ├── AdminOpportunities.tsx# Career & placement portal management
│           └── AdminAnalytics.tsx    # Deep analytics on AI inquiries & SLAs
```

---

## Installation & Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Create or inspect `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME="Paavai Smart Campus AI"
VITE_ENABLE_MOCK_FALLBACK=true
```

### 3. Run Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173/`.

### 4. Build for Production
```bash
npm run build
```

---

## Complete Hackathon Demonstration Script

### Step 1: Login & Student Dashboard
1. Open `http://localhost:5173/`.
2. Notice the **1-Click Demo Evaluation Profiles** on the login page. Click **"Student"** (Krishna S, CSE 3rd Year).
3. The **Student Dashboard** displays:
   - Personalized welcome message with branch, semester, and register number.
   - Quick action launcher (Ask AI, Report a Problem, Announcements, Opportunities, Submit Request).
   - Important announcements ticker from the Controller of Examinations and Placement Cell.
   - Active grievance ticket summary, upcoming events, and academic deadlines.

### Step 2: Test Verified AI Campus Assistant
1. Click **"Ask AI"** in the top navigation or dashboard.
2. Select or type:  
   *“What is the procedure for applying for a bonafide certificate?”*
3. The AI assistant returns:
   - Green **Verified College Source** badge with 98% confidence score.
   - Detailed step-by-step procedure (ERP request, HOD endorsement, 24-hr issuance, Admin Window 3).
   - Clickable source citations referencing *“Official Bonafide & Certificates Procedure Manual (Circular Ref: PI/ADM/2024-91), Page 4”*.
4. Test an ungrounded or unofficial question to see the safety guardrail in action:
   - Displays: *“Unable to verify this information from official college sources.”*

### Step 3: Smart AI Grievance Creation
1. Return to the dashboard or grievances page and click **"Report a Problem (Smart AI)"**.
2. Type in the description:  
   *“CSE lab projector is not working properly. Lamp flickers and HDMI display drops during lecture.”*
3. Observe the real-time AI auto-triage card appear dynamically:
   - **AI Detected Category**: `Infrastructure`
   - **Priority**: `Medium`
   - **Target Department**: `CSE`
   - **Confidence**: `94%`
4. Click **"Confirm & Submit Ticket"**. A toast notification confirms ticket creation (`GRV-2025-0104`).

### Step 4: Faculty & Admin Triage
1. Use the **Role Selector** in the header or sidebar to switch to **"Faculty"** (Sundar C - HOD CSE) or **"Admin"** (Ramasamy C V - Registrar).
2. On the **Faculty Dashboard**:
   - View assigned department tickets, including the newly created projector issue.
   - Click **"Manage"** -> update status from `Assigned` to `In Progress` or `Resolved`, and add an official technician note.
   - Review pending student requests (approve Bonafide or OD requests).
3. On the **Admin Dashboard**:
   - Inspect department workload charts and resolution trends.
   - Navigate to `/admin/documents` (**Document Knowledge Base**) to view official circulars with processing statuses (`Uploaded` -> `Processing` -> `Indexed` -> `Verified`).
   - Note that internal vector embeddings are kept secure on the backend server.
4. Switch back to **"Student"** view to verify the ticket's updated status timeline.

---

## API Integration Points & Backend Architecture

The application is structured to connect seamlessly to a FastAPI / Express / Ollama backend:

| Service Module | Method | HTTP Endpoint | Description |
|---|---|---|---|
| `authApi` | `POST` | `/auth/login` | JWT login with role tokens |
| `authApi` | `GET` | `/auth/me` | Fetch active profile |
| `aiApi` | `POST` | `/ai/chat` | RAG retrieval returning answer, sources, verified flag |
| `aiApi` | `POST` | `/ai/grievance/classify` | NLP extraction returning category, priority, department |
| `grievanceApi` | `GET` | `/grievances` | List tickets with filters (department, studentId, status) |
| `grievanceApi` | `POST` | `/grievances` | Create new ticket |
| `grievanceApi` | `PATCH`| `/grievances/:id/status` | Transition status with actor note |
| `announcementApi`| `GET` | `/announcements` | Filter by category, search, important badge |
| `opportunityApi` | `GET` | `/opportunities` | Fetch opportunities with match percentage |
| `documentApi` | `GET` | `/admin/documents` | Knowledge base document inventory |
| `documentApi` | `POST`| `/admin/documents/upload` | Multipart file upload (PDF/DOCX/TXT) |
| `documentApi` | `POST`| `/admin/documents/:id/index` | Trigger RAG chunking & vector indexing |
| `documentApi` | `POST`| `/admin/documents/:id/verify`| Mark document as official ground truth |

### Remaining Backend Dependencies (When integrating live Python/Node backend):
1. **Ollama / LLM Runner**: Running locally or on server (`http://localhost:11434` with model `llama3:8b` or `deepseek-r1:8b`).
2. **Vector DB / Store**: ChromaDB / Qdrant / FAISS for storing document chunk embeddings.
3. **Document Parser**: `pypdf`, `python-docx` for extracting text from uploaded campus circulars.
4. **Relational Database**: PostgreSQL / SQLite for persistent grievance tickets, users, and announcements.
#   P a a v a i - S m a r t - C a m p u s  
 