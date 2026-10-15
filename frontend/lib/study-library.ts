import { api } from "@/lib/api";
import { authenticatedFetch } from "@/lib/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Subject {
  id: string; code: string; name: string; institution: string; source_note: string; is_active: boolean;
}

export interface StudyFile {
  id: string; original_name: string; mime_type: string; extension: string; size_bytes: number;
}

export interface StudyDocument {
  id: string; group_id: string; subject_id: string; subject_code: string; subject_name: string;
  uploaded_by: string; uploader_name: string; title: string; description: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED"; total_bytes: number;
  reviewed_at: string | null; rejection_reason: string | null; created_at: string;
  files: StudyFile[];
}

export const searchSubjects = (q = "") => api<Subject[]>(`/subjects?q=${encodeURIComponent(q)}`);
export const adminSubjects = (q = "") => api<Subject[]>(`/admin/subjects?q=${encodeURIComponent(q)}`);
export const saveSubject = (body: Pick<Subject, "code" | "name" | "source_note" | "is_active">) =>
  api<Subject>("/admin/subjects", { method: "PUT", body: JSON.stringify(body) });

export const listStudyDocuments = (groupId: string, q = "", subjectId = "", offset = 0) =>
  api<StudyDocument[]>(`/groups/${groupId}/library?q=${encodeURIComponent(q)}${subjectId ? `&subject_id=${subjectId}` : ""}&offset=${offset}`);
export const myStudyDocuments = (groupId: string, offset = 0) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/mine?offset=${offset}`);
export const pendingStudyDocuments = (groupId: string, offset = 0) =>
  api<StudyDocument[]>(`/groups/${groupId}/library/admin/pending?offset=${offset}`);

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
