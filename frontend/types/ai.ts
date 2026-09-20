export interface AICitation {
  order: number;
  title: string;
  source_url: string | null;
  page_start: number | null;
  page_end: number | null;
  section_title: string | null;
  relevance_score: number;
}

export interface AIChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  refused: boolean;
  refusal_reason: string | null;
  citations: AICitation[];
  rewritten_question: string;
}

export interface AIConversation {
  id: string;
  title: string | null;
  academic_year_context: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIMessage {
  id: string;
  sequence_number: number;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | string;
  content: string;
  rewritten_question: string | null;
  created_at: string;
  citations?: AICitation[];
}

export interface AIConversationMessages {
  conversation: AIConversation;
  messages: AIMessage[];
}
