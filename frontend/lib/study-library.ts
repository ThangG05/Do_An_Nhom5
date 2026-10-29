import { api } from "@/lib/api";
import { authenticatedFetch } from "@/lib/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Subject {
  id: string; code: string | null; name: string; institution: string; source_note: string; is_active: boolean;
  category: "GENERAL" | "SPECIALIZED"; needs_review: boolean; major_ids: string[];
}
export interface Major { id: string; code: string | null; name: string; subject_count: number; }
export type DocumentType = "EXAM" | "EXERCISE" | "LECTURE" | "REVIEW" | "OTHER";
export type AssessmentType = "MIDTERM" | "FINAL";
export const documentTypeLabel: Record<DocumentType, string> = {
  EXAM: "Đề thi / Kiểm tra", EXERCISE: "Bài tập / Thực hành",
  LECTURE: "Giáo trình / Bài giảng", REVIEW: "Đề cương / Ôn tập", OTHER: "Tài liệu khác",
};
export const assessmentTypeLabel: Record<AssessmentType, string> = {
  MIDTERM: "Giữa kỳ", FINAL: "Cuối kỳ",
};
export interface CatalogScope { category?: "GENERAL" | "SPECIALIZED" | ""; majorId?: string; }
const scopeParams = (scope: CatalogScope) => `${scope.category ? `&category=${scope.category}` : ""}${scope.majorId ? `&major_id=${encodeURIComponent(scope.majorId)}` : ""}`;
export const listMajors = () => api<Major[]>("/majors");

export interface StudyFile {
  id: string; original_name: string; mime_type: string; extension: string; size_bytes: number;
}

export interface StudyDocument {
  id: string; group_id: string; subject_id: string; subject_code: string | null; subject_name: string;
  major_id: string | null; document_type: DocumentType | null; assessment_type: AssessmentType | null;
  uploaded_by: string; uploader_name: string; title: string; description: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED"; total_bytes: number;
  reviewed_at: string | null; rejection_reason: string | null; created_at: string;
  files: StudyFile[];
}
export interface StudyDuplicateMatch {
  sha256: string; duplicate_count: number; pending_count: number; approved_count: number;
}
export interface StudyAIFileAssessment {
  file_id: string; file_name: string;
  subject_relevance: "RELEVANT" | "IRRELEVANT" | "UNCERTAIN";
  content_type: "ACADEMIC" | "SPAM" | "UNCERTAIN";
  recommendation: "APPROVE" | "REJECT" | "REVIEW";
  evidence_quote: string | null; evidence_location: string | null;
  copyright_status?: "SUSPECTED" | "UNCERTAIN";
  copyright_evidence?: string | null; copyright_reason?: string;
  attribution_signals?: string[]; embedded_metadata?: Record<string, string>;
  reason: string; error_code: string | null;
  sampling_limited: boolean;
}
export interface StudyAIAssessment {
  document_id: string; status: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";
  recommendation: "APPROVE" | "REJECT" | "REVIEW" | null;
  file_results: StudyAIFileAssessment[] | null; reason: string | null; completed_at: string | null;
}

export interface StudyDocumentReport {
  id: string; group_id: string; document_id: string; title: string; subject_code: string | null;
  subject_name: string; uploader_name: string; reporter_name: string; reason: string;
  status: "OPEN" | "RESOLVED" | "DISMISSED"; resolution_note: string | null;
  handled_by_name: string | null; created_at: string; document_deleted: boolean;
}

export const searchSubjects = (q = "", scope: CatalogScope = {}, offset = 0, limit = 8) => api<Subject[]>(`/subjects?q=${encodeURIComponent(q)}${scopeParams(scope)}&limit=${limit}&offset=${offset}`);
export const adminSubjects = (groupId: string, q = "", offset = 0, limit = 11) => api<Subject[]>(`/groups/${groupId}/library/admin/subjects?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`);
export const saveSubject = (groupId: string, body: Pick<Subject, "code" | "name" | "source_note" | "is_active"> & Partial<Pick<Subject, "id" | "category" | "needs_review" | "major_ids">>) =>
  api<Subject>(`/groups/${groupId}/library/admin/subjects`, { method: "PUT", body: JSON.stringify(body) });

export const listStudyDocuments = (groupId: string, q = "", subjectId = "", offset = 0, scope: CatalogScope = {}, limit = 6,
  documentType = "", assessmentType = "") =>
  api<StudyDocument[]>(`/groups/${groupId}/library?q=${encodeURIComponent(q)}${subjectId ? `&subject_id=${subjectId}` : ""}&limit=${limit}&offset=${offset}${scopeParams(scope)}${documentType ? `&document_type=${documentType}` : ""}${assessmentType ? `&assessment_type=${assessmentType}` : ""}`);
export const myStudyDocuments = (groupId: string, offset = 0, limit = 6) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/mine?limit=${limit}&offset=${offset}`);
export const pendingStudyDocuments = (groupId: string, offset = 0, limit = 6) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/admin/pending?limit=${limit}&offset=${offset}`);
export const pendingStudyDocumentCount = (groupId: string) =>
  api<{ count: number }>(`/groups/${groupId}/library/admin/pending-count`);
export const checkStudyFileDuplicates = (groupId: string, checksums: string[]) =>
  api<{ matches: StudyDuplicateMatch[] }>(`/groups/${groupId}/library/check-duplicates`, {
    method: "POST", body: JSON.stringify({ checksums }),
  });
export const pendingStudyAIAssessments = (groupId: string, ids: string[]) =>
  api<StudyAIAssessment[]>(`/groups/${groupId}/library/admin/ai-assessments?${ids.map(id => `document_ids=${encodeURIComponent(id)}`).join("&")}`);
export const openStudyDocumentReportCount = (groupId: string) =>
  api<{ count: number }>(`/groups/${groupId}/library/admin/reports/count`);
export const openStudyDocumentReports = (groupId: string, offset = 0, limit = 50) =>
  api<StudyDocumentReport[]>(`/groups/${groupId}/library/admin/reports?limit=${limit}&offset=${offset}`);
export const reportStudyDocument = (groupId: string, documentId: string, reason: string) =>
  api<{ id: string; status: "OPEN" }>(`/groups/${groupId}/library/${documentId}/reports`, {
    method: "POST", body: JSON.stringify({ reason }),
  });
export const decideStudyDocumentReport = (groupId: string, reportId: string,
  decision: "REMOVE_DOCUMENT" | "DISMISS", note: string) =>
  api<{ id: string; status: "RESOLVED" | "DISMISSED"; document_id: string }>(
    `/groups/${groupId}/library/admin/reports/${reportId}`,
    { method: "PATCH", body: JSON.stringify({ decision, note }) },
  );

export async function shareStudyDocument(groupId: string, majorId: string, subjectId: string,
  documentType: DocumentType, assessmentType: AssessmentType | null, title: string,
  description: string, files: File[]): Promise<StudyDocument> {
  const body = new FormData();
  body.append("major_id", majorId); body.append("subject_id", subjectId);
  body.append("document_type", documentType);
  if (assessmentType) body.append("assessment_type", assessmentType);
  body.append("title", title); body.append("description", description);
  files.forEach(file => body.append("files", file));
  const response = await authenticatedFetch(`${BASE}/groups/${groupId}/library`, { method: "POST", body });
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(error?.detail || "Không thể gửi tài liệu.");
  }
  return response.json() as Promise<StudyDocument>;
}

export const decideStudyDocument = (groupId: string, documentId: string, decision: "APPROVE" | "REJECT", reason?: string) =>
  api<StudyDocument>(`/groups/${groupId}/library/admin/${documentId}`, {
    method: "PATCH", body: JSON.stringify({ decision, reason }),
  });

export const signedStudyFile = (groupId: string, documentId: string, fileId: string, preview: boolean) =>
  api<{ url: string; expires_in: number }>(`/groups/${groupId}/library/${documentId}/files/${fileId}/download?preview=${preview}`);

export const previewStudyOfficeFile = (groupId: string, documentId: string, fileId: string) =>
  api<OfficePreview>(`/groups/${groupId}/library/${documentId}/files/${fileId}/preview-office`);

export const deleteStudyDocument = (groupId: string, documentId: string) =>
  api<void>(`/groups/${groupId}/library/${documentId}`, { method: "DELETE" });

export type OfficePreview =
  | { kind: "word"; name: string; paragraphs: string[]; tables: string[][][] }
  | { kind: "excel"; name: string; sheets: { name: string; rows: (string | null)[][]; truncated: boolean }[] }
  | { kind: "presentation"; name: string; slides: { number: number; text: string }[]; truncated: boolean };

export async function downloadStudyBundle(groupId: string, documentId: string): Promise<Blob> {
  const response = await authenticatedFetch(`${BASE}/groups/${groupId}/library/${documentId}/download-bundle`);
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(error?.detail || "Không thể tải trọn bộ tài liệu.");
  }
  return response.blob();
}
