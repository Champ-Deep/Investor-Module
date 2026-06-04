import axios from "axios";

import type {
  Freshness,
  FirmProfile,
  ParsedQuery,
  QueryFilters,
  SearchResponse,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

export const parseQuery = (query: string) =>
  api.post<ParsedQuery>("/parse", { query }).then((r) => r.data);

export const search = (filters: QueryFilters) =>
  api.post<SearchResponse>("/search", filters).then((r) => r.data);

export const getFirm = (slug: string) =>
  api.get<FirmProfile>(`/firms/${slug}`).then((r) => r.data);

export const getFreshness = () =>
  api.get<Freshness>("/freshness").then((r) => r.data);

export interface AppStatus {
  llm_parse: string;
  llm_model: string | null;
  embeddings: string;
  data_source: string;
  contact_sla_days: number;
  firms_loaded: number;
}

export const getStatus = () => api.get<AppStatus>("/status").then((r) => r.data);
