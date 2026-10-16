import { api } from "@/lib/api";
import { authenticatedFetch } from "@/lib/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Subject {
  id: string; code: string | null; name: string; institution: string; source_note: string; is_active: boolean;
  category: "GENERAL" | "SPECIALIZED"; needs_review: boolean; major_ids: string[];
}
export interface Major { id: string; code: string | null; name: string; subject_count: number; }
export interface CatalogScope { category?: "GENERAL" | "SPECIALIZED" | ""; majorId?: string; }
const scopeParams = (scope: CatalogScope) => `${scope.category ? `&category=${scope.category}` : ""}${scope.majorId ? `&major_id=${encodeURIComponent(scope.majorId)}` : ""}`;
export const listMajors = () => api<Major[]>("/majors");

export interface StudyFile {
  id: string; original_name: string; mime_type: string; extension: string; size_bytes: number;
}

export interface StudyDocument {
  id: string; group_id: string; subject_id: string; subject_code: string | null; subject_name: string;
  uploaded_by: string; uploader_name: string; title: string; description: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED"; total_bytes: number;
  reviewed_at: string | null; rejection_reason: string | null; created_at: string;
  files: StudyFile[];
}

export const searchSubjects = (q = "", scope: CatalogScope = {}, offset = 0, limit = 8) => api<Subject[]>(`/subjects?q=${encodeURIComponent(q)}${scopeParams(scope)}&limit=${limit}&offset=${offset}`);
export const adminSubjects = (q = "", offset = 0) => api<Subject[]>(`/admin/subjects?q=${encodeURIComponent(q)}&offset=${offset}`);
export const saveSubject = (body: Pick<Subject, "code" | "name" | "source_note" | "is_active"> & Partial<Pick<Subject, "id" | "category" | "needs_review" | "major_ids">>) =>
  api<Subject>("/admin/subjects", { method: "PUT", body: JSON.stringify(body) });

export const listStudyDocuments = (groupId: string, q = "", subjectId = "", offset = 0, scope: CatalogScope = {}, limit = 6) =>
  api<StudyDocument[]>(`/groups/${groupId}/library?q=${encodeURIComponent(q)}${subjectId ? `&subject_id=${subjectId}` : ""}&limit=${limit}&offset=${offset}${scopeParams(scope)}`);
export const myStudyDocuments = (groupId: string, offset = 0, limit = 6) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/mine?limit=${limit}&offset=${offset}`);
export const pendingStudyDocuments = (groupId: string, offset = 0, limit = 6) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/admin/pending?limit=${limit}&offset=${offset}`);
export const pendingStudyDocumentCount = (groupId: string) =>
  api<{ count: number }>(`/groups/${groupId}/library/admin/pending-count`);

export async function shareStudyDocument(groupId: string, subjectId: string, title: string,
                                         description: string, files: File[]): Promise<StudyDocument> {
  const body = new FormData();
  body.append("subject_id", subjectId); body.append("title", title); body.append("description", description);
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
  | { kind: "excel"; name: string; sheets: { name: string; rows: (string | null)[][]; truncated: boolean }[] };

export async function downloadStudyBundle(groupId: string, documentId: string): Promise<Blob> {
  const response = await authenticatedFetch(`${BASE}/groups/${groupId}/library/${documentId}/download-bundle`);
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(error?.detail || "Không thể tải trọn bộ tài liệu.");
  }
  return response.blob();
}
