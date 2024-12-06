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
  conclusion?: Section[];
  action_items?: string[];
  summary?: string;
}

export interface Message {
  role: string;
  content?: StructuredContent;
  simpleMessage?: string;
  type: string;
}

export interface Insight {
  title?: string;
  description?: string;
  actions?: string[];
}
