/**
 * Help Center Types
 */

export interface HelpArticle {
  id: number;
  title: string;
  content: string;
  category: string;
  tags: string[];
  views: number;
  created_at: string;
  updated_at: string;
}

export interface HelpCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  article_count: number;
}

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  helpful_count: number;
}
