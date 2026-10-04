import api from './client';
import type { Page, UUID } from './types';

export type TournamentStatus = 'draft' | 'registration' | 'in_progress' | 'completed' | 'cancelled';

export interface Tournament {
  id: UUID;
  organizer_id: UUID;
  name: string;
  description: string | null;
  category: string;
  format: string;
  status: TournamentStatus;
  max_entries: number;
  entry_fee_cents: number;
  currency: string;
  starts_at: string | null;
  ends_at: string | null;
  venue_id: UUID | null;
  created_at: string;
}

export interface TournamentEntry {
  id: UUID;
  tournament_id: UUID;
  user_id: UUID;
  seed: number | null;
  status: string;
  created_at: string;
}

export interface StandingRow {
  entry_id: UUID;
  user_id: UUID;
  played: number;
  won: number;
  lost: number;
  points: number;
  rank: number;
}

export interface TournamentStandings {
  tournament_id: UUID;
  status: TournamentStatus;
  standings: StandingRow[];
}

export interface BracketMatch {
  id: UUID;
  round_number: number;
  slot: number;
  home_entry_id: UUID | null;
  away_entry_id: UUID | null;
  winner_entry_id: UUID | null;
  match_id: UUID | null;
  status: string;
}

export interface TournamentBracket {
  tournament_id: UUID;
  format: string;
  rounds: number;
  matches: BracketMatch[];
}

export interface TournamentFilters {
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function listTournaments(filters: TournamentFilters = {}): Promise<Page<Tournament>> {
  const { data } = await api.get<Page<Tournament>>('/api/v1/tournaments', { params: filters });
  return data;
}

export async function getTournament(id: string): Promise<Tournament> {
  const { data } = await api.get<Tournament>(`/api/v1/tournaments/${id}`);
  return data;
}

export async function listEntries(id: string): Promise<TournamentEntry[]> {
  const { data } = await api.get<TournamentEntry[]>(`/api/v1/tournaments/${id}/entries`);
  return data;
}

export async function getStandings(id: string): Promise<TournamentStandings> {
  const { data } = await api.get<TournamentStandings>(`/api/v1/tournaments/${id}/standings`);
  return data;
}

export async function getBracket(id: string): Promise<TournamentBracket> {
  const { data } = await api.get<TournamentBracket>(`/api/v1/tournaments/${id}/bracket`);
  return data;
}

export async function registerForTournament(id: string): Promise<TournamentEntry> {
  const { data } = await api.post<TournamentEntry>(`/api/v1/tournaments/${id}/register`);
  return data;
}

export async function unregisterFromTournament(id: string): Promise<void> {
  await api.delete(`/api/v1/tournaments/${id}/register`);
}
