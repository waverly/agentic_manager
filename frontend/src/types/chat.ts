/* eslint-disable @typescript-eslint/no-explicit-any */
export interface Section {
  heading?: string;
  points: Point[];
}

export interface Point {
  text: string;
  citations: any[];
}

export interface Card {
  title: string;
  description: string;
  actions: string[];
}

export interface StructuredContent {
  title?: string;
  sections?: Section[];
  insights?: Card[];
}

export interface Message {
  role: string;
  type: string;
  content: StructuredContent;
}

export interface Insight {
  title?: string;
  description?: string;
  actions?: string[];
}
