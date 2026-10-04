/** Domain types mirroring the FastAPI Pydantic schemas (snake_case wire format). */

export type UUID = string;

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type ActivityCategory =
  | 'racket'
  | 'team'
  | 'combat'
  | 'strength'
  | 'running'
  | 'cycling'
  | 'water'
  | 'winter'
  | 'precision'
  | 'gymnastics'
  | 'outdoor'
  | 'other';

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert' | 'any';
export type ActivityVisibility = 'public' | 'unlisted' | 'private';
export type ParticipantStatus =
  | 'invited'
  | 'requested'
  | 'confirmed'
  | 'waitlisted'
  | 'declined'
  | 'cancelled'
  | 'attended'
  | 'no_show';
export type BookingStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'refunded';
export type PaymentStatus =
  | 'pending'
  | 'authorized'
  | 'paid'
  | 'failed'
  | 'refunded'
  | 'cancelled';
export type SplitStatus = 'pending' | 'paid' | 'waived' | 'refunded';

export interface Profile {
  id: UUID;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  city: string | null;
  country: string | null;
  skill_level: SkillLevel;
  reputation_score: number;
}

export interface User {
  id: UUID;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  email_verified: boolean;
  created_at: string;
  profile: Profile | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface ActivityVenueRef {
  id: UUID;
  name: string;
  city: string;
}

export interface Activity {
  id: UUID;
  host_id: UUID;
  venue_id: UUID | null;
  club_id: UUID | null;
  category_link_id: UUID | null;
  title: string;
  /** Slug of the activity type (e.g. 'padel'). Added in the Phase-2 API. */
  activity_type?: string | null;
  /** Embedded venue reference (name + city) so cards can show the venue. */
  venue?: ActivityVenueRef | null;
  description: string | null;
  category: ActivityCategory;
  sport_category?: string | null;
  sport_slug?: string | null;
  skill_level: SkillLevel;
  visibility: ActivityVisibility;
  starts_at: string;
  ends_at: string | null;
  max_participants: number;
  cost_per_person_cents: number;
  currency: string;
  is_cancelled: boolean;
  created_at: string;
  participant_count: number;
}

export interface ActivityParticipant {
  id: UUID;
  activity_id: UUID;
  user_id: UUID;
  status: ParticipantStatus;
  is_host: boolean;
  joined_at: string | null;
}

export interface ActivityCreateInput {
  title: string;
  description?: string;
  category: ActivityCategory;
  skill_level?: SkillLevel;
  visibility?: ActivityVisibility;
  venue_id?: UUID | null;
  starts_at: string;
  ends_at?: string | null;
  max_participants?: number;
  cost_per_person_cents?: number;
  currency?: string;
  /** Optional cover image URL returned by POST /api/v1/media/upload. */
  cover_url?: string;
}

export interface Venue {
  id: UUID;
  owner_id: UUID | null;
  name: string;
  description: string | null;
  address_line: string | null;
  city: string;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  timezone: string;
  is_active: boolean;
  created_at: string;
  court_count: number;
}

export interface VenueAvailability {
  id: UUID;
  weekday: number;
  opens_at: string;
  closes_at: string;
  is_active: boolean;
}

export interface VenueCourt {
  id: UUID;
  venue_id: UUID;
  name: string;
  surface: string | null;
  capacity: number;
  hourly_price_cents: number;
  is_active: boolean;
  availability: VenueAvailability[];
}

export interface Club {
  id: UUID;
  owner_id: UUID;
  slug: string;
  name: string;
  description: string | null;
  category: ActivityCategory;
  city: string | null;
  is_public: boolean;
  created_at: string;
  member_count: number;
}

export interface ClubMember {
  id: UUID;
  club_id: UUID;
  user_id: UUID;
  role: string;
  is_active: boolean;
  joined_at: string | null;
}

export interface PaymentSplit {
  id: UUID;
  payment_id: UUID;
  booking_id: UUID | null;
  user_id: UUID;
  share_cents: number;
  currency: string;
  status: SplitStatus;
}

export interface Payment {
  id: UUID;
  booking_id: UUID | null;
  payer_id: UUID;
  amount_cents: number;
  currency: string;
  status: PaymentStatus;
  provider: string;
  provider_reference: string | null;
  splits: PaymentSplit[];
}

export interface Booking {
  id: UUID;
  venue_court_id: UUID | null;
  activity_id: UUID | null;
  booked_by_id: UUID;
  status: BookingStatus;
  starts_at: string;
  ends_at: string;
  total_price_cents: number;
  currency: string;
  idempotency_key: string | null;
  created_at: string;
  payments: Payment[];
  splits: PaymentSplit[];
}

export interface Balance {
  booking_id: UUID;
  currency: string;
  total_cents: number;
  paid_cents: number;
  outstanding_cents: number;
}

export interface BookingCreateInput {
  venue_court_id?: UUID | null;
  activity_id?: UUID | null;
  starts_at: string;
  ends_at: string;
  currency?: string;
  idempotency_key?: string;
  total_price_cents?: number;
  split_between_user_ids?: UUID[];
}

export interface LeaderboardEntry {
  id: UUID;
  user_id: UUID;
  category: string;
  period: string;
  rank: number;
  rating: number;
  games_played: number;
  computed_at: string | null;
}

export interface MmrRating {
  id: UUID;
  user_id: UUID;
  category: string;
  rating: number;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
}

export interface MmrHistory {
  id: UUID;
  user_id: UUID;
  match_result_id: UUID | null;
  rating_before: number;
  rating_after: number;
  delta: number;
  reason: string;
  created_at: string;
}

export interface UserRatings {
  user_id: UUID;
  ratings: MmrRating[];
  history: MmrHistory[];
}

export interface Match {
  id: UUID;
  activity_id: UUID | null;
  tournament_id: UUID | null;
  status: string;
  scheduled_at: string | null;
  played_at: string | null;
  participants: Array<{
    id: UUID;
    user_id: UUID;
    team: number;
    is_winner: boolean | null;
    score: number;
  }>;
  results: Array<{
    id: UUID;
    match_id: UUID;
    submitted_by_id: UUID;
    status: string;
    team_a_score: number;
    team_b_score: number;
    winner_team: number | null;
    notes: string | null;
    mmr_applied: boolean;
    verified_at: string | null;
  }>;
}

export interface Notification {
  id: UUID;
  user_id: UUID;
  type: string;
  title: string;
  body: string | null;
  data: Record<string, unknown> | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPage {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface Health {
  status: string;
  version: string;
  db: string;
}

/* ------------------------------------------------------------------ *
 * Discovery (Phase-3): matchmaking, progress/streak, venue map.
 * ------------------------------------------------------------------ */

export interface MatchmakingActivity {
  id: UUID;
  title: string;
  category: ActivityCategory;
  sport_slug: string | null;
  sport_category: string | null;
  city: string | null;
  venue_name: string | null;
  starts_at: string;
  cost_per_person_cents: number;
  currency: string;
  participant_count: number;
  max_participants: number;
  skill_level: SkillLevel;
  match_score: number;
  reason: string;
}

export interface MatchmakingPartner {
  user_id: UUID;
  display_name: string;
  city: string | null;
  shared_categories: string[];
  category: string;
  rating: number | null;
  games_played: number;
  match_score: number;
}

export interface MatchmakingResponse {
  city: string | null;
  interests: string[];
  activities: MatchmakingActivity[];
  partners: MatchmakingPartner[];
}

export interface StreakAchievement {
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  points: number;
  target: number;
  progress: number;
  earned: boolean;
  earned_at: string | null;
}

export interface WeeklyCount {
  week_start: string;
  count: number;
}

export interface DayCount {
  date: string;
  count: number;
}

export interface UserProgress {
  user_id: UUID;
  current_streak: number;
  longest_streak: number;
  total_active_days: number;
  last_active_date: string | null;
  activities_joined: number;
  activities_hosted: number;
  matches_played: number;
  distinct_categories: number;
  weekly: WeeklyCount[];
  calendar: DayCount[];
  achievements: StreakAchievement[];
}

export interface MapVenue {
  id: UUID;
  name: string;
  city: string;
  province: string | null;
  area: string | null;
  category: string | null;
  venue_kind: string | null;
  latitude: number;
  longitude: number;
  court_count: number;
  sport_slugs: string[];
}

export interface VenueMapBounds {
  min_lat: number;
  max_lat: number;
  min_lng: number;
  max_lng: number;
}

export interface VenueMapResponse {
  count: number;
  bounds: VenueMapBounds;
  venues: MapVenue[];
}

/* ---- Follows / friends ---- */

export interface FollowUser {
  user_id: string;
  username: string;
  display_name: string;
  city?: string | null;
  avatar_url?: string | null;
  category?: string | null;
  rating?: number | null;
  games_played: number;
  is_following: boolean;
  is_friend: boolean;
}

export interface FollowList {
  items: FollowUser[];
  total: number;
}

export interface FollowCounts {
  followers: number;
  following: number;
  friends: number;
}
